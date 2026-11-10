"""Score MIMIC-IV-ECG with frozen SPH PAC probes against machine-report mentions."""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.mimic_ecg_reports import (
    iter_mimic_machine_reports,
    verify_mimic_sha256_manifest,
)
from titan_v45.data.mimic_ecg_waveform import (
    prepare_mimic_waveform,
    resolve_mimic_record_base,
)
from titan_v45.evaluation.mimic_concordance import summarize_mimic_pac_concordance
from titan_v45.evaluation.pac_probe import (
    pool_record_windows,
    pool_v3f_tokens,
    predict_logistic_probe,
    predict_mlp_probe,
)
from titan_v45.evaluation.provenance import (
    read_required_sha256_environment,
    verify_implementation_sha256,
    verify_runtime_versions,
)
from titan_v45.models.v3f_embeddings import V3FTokenEmbeddingExtractor, sha256_file

CONFIG_RELATIVE = "configs/external_validation/pac_v3f_embedding_probe.json"


def _verify_tree(repo, expected_commit, expected_config_sha256):
    config_path = repo / CONFIG_RELATIVE
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                            capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, check=True,
                            capture_output=True, text=True).stdout.strip()
    if commit != expected_commit or status:
        raise ValueError("protocol checkout must be clean and match the frozen commit")
    config_hash = sha256_file(config_path)
    if config_hash != expected_config_sha256:
        raise ValueError("PAC protocol configuration SHA-256 mismatch")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    verify_implementation_sha256(repo, config.get("implementation_sha256", {}))
    return config, config_hash, commit


def _load_probe_bundle(path, expected_sha256, *, commit, config_hash, model_sha256):
    if sha256_file(path) != expected_sha256:
        raise ValueError("private PAC probe bundle SHA-256 mismatch")
    bundle = torch.load(path, map_location="cpu", weights_only=True)
    if (not isinstance(bundle, dict)
            or bundle.get("schema") != "TITAN_V45_PAC_PROBE_MODEL_BUNDLE_PRIVATE_V1"
            or bundle.get("protocol_commit") != commit
            or bundle.get("protocol_config_sha256") != config_hash
            or bundle.get("v3f_checkpoint_sha256") != model_sha256):
        raise ValueError("private PAC probe bundle is not linked to the frozen protocol")
    logistic_source, mlp_source = bundle.get("logistic"), bundle.get("mlp")
    if not isinstance(logistic_source, dict) or not isinstance(mlp_source, dict):
        raise ValueError("private PAC probe bundle lacks both frozen probes")
    logistic = {
        "mean": logistic_source["mean"].cpu().numpy(),
        "scale": logistic_source["scale"].cpu().numpy(),
        "coefficient": logistic_source["coefficient"].cpu().numpy(),
        "intercept": float(logistic_source["intercept"]),
    }
    mlp = {
        **{key: mlp_source[key] for key in (
            "input_dim", "seed", "epochs", "batch_size", "learning_rate",
            "weight_decay", "dropout",
        )},
        "mean": mlp_source["mean"].cpu().numpy(),
        "scale": mlp_source["scale"].cpu().numpy(),
        "state_dict": mlp_source["state_dict"],
    }
    if (logistic["mean"].shape != (1280,) or logistic["scale"].shape != (1280,)
            or logistic["coefficient"].shape != (1280,) or mlp["input_dim"] != 1280
            or mlp["mean"].shape != (1280,) or mlp["scale"].shape != (1280,)):
        raise ValueError("private PAC probe bundle has unexpected feature dimensions")
    arrays = (logistic["mean"], logistic["scale"], logistic["coefficient"],
              mlp["mean"], mlp["scale"])
    if (not all(np.isfinite(values).all() for values in arrays)
            or np.any(logistic["scale"] <= 0) or np.any(mlp["scale"] <= 0)
            or not np.isfinite(logistic["intercept"])):
        raise ValueError("private PAC probe bundle contains nonfinite or nonpositive parameters")
    state_dict = mlp["state_dict"]
    if (not isinstance(state_dict, dict) or not state_dict
            or any(not torch.is_tensor(value) or not torch.isfinite(value).all()
                   for value in state_dict.values())):
        raise ValueError("private PAC probe bundle contains invalid MLP parameters")
    return logistic, mlp


def _failure_reason(exc):
    message = str(exc).lower()
    if "500 hz" in message or "10-second" in message:
        return "mimic_duration_or_sample_rate_mismatch"
    if "mV units" in message:
        return "mimic_physical_unit_mismatch"
    if "canonical 12-lead" in message or "mapped" in message:
        return "mimic_lead_mapping_failure"
    if "nonfinite" in message or "finite" in message:
        return "mimic_nonfinite_signal"
    if "missing or unsafe" in message or "wfdb" in message or "header" in message:
        return "mimic_wfdb_read_failure"
    return "mimic_preprocessing_failure"


def _flush(pending, extractor, logistic, mlp, batch_size, scores):
    if not pending:
        return
    windows = [sample for _index, prepared in pending for sample in prepared["windows"]]
    tokens = extractor.extract_windows(windows, batch_size=batch_size)
    window_vectors = pool_v3f_tokens(tokens)
    features = []
    cursor = 0
    for _index, prepared in pending:
        count = len(prepared["windows"])
        features.append(pool_record_windows(window_vectors[cursor:cursor + count]))
        cursor += count
    if cursor != len(window_vectors):
        raise RuntimeError("MIMIC token window accounting mismatch")
    feature_matrix = np.stack(features).astype(np.float32, copy=False)
    predictions = {
        "weighted_l2_logistic": predict_logistic_probe(feature_matrix, logistic),
        "fixed_mlp_sensitivity": predict_mlp_probe(feature_matrix, mlp),
    }
    if any(values.shape != (len(pending),) or not np.isfinite(values).all()
           for values in predictions.values()):
        raise RuntimeError("frozen PAC probe emitted invalid MIMIC scores")
    for offset, (index, _prepared) in enumerate(pending):
        for name, values in predictions.items():
            scores[name][index] = float(values[offset])


def _write_exclusive(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def run(args):
    import wfdb

    repo, source, release = args.repo.resolve(), args.source.resolve(), args.release_root.resolve()
    model_bundle = args.private_model_bundle.resolve()
    output_dir = args.output_dir.resolve()
    if (source.is_relative_to(repo) or repo.is_relative_to(source)
            or model_bundle.is_relative_to(repo) or not output_dir.is_relative_to(repo)):
        raise ValueError("MIMIC source and private model must stay outside Git")
    aggregate_path = output_dir / "mimic_pac_machine_report_aggregate.json"
    receipt_path = output_dir / "mimic_pac_machine_report_receipt.json"
    if aggregate_path.exists() or receipt_path.exists():
        raise FileExistsError("MIMIC aggregate output already exists")

    config, config_hash, commit = _verify_tree(
        repo, args.expected_commit, args.expected_config_sha256
    )
    dependency_hashes = read_required_sha256_environment({
        "python_deps": "TITAN_PYTHON_DEPS_SHA256",
    }, expected_hashes=config["environment"]["dependency_archive_sha256"])
    runtime_versions = verify_runtime_versions({
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "wfdb": wfdb.__version__,
    }, config["environment"]["versions"])
    mimic = config["mimic_iv_ecg_v1"]
    if mimic["complete_download_authorized"] is not True:
        raise PermissionError("MIMIC scoring is blocked pending CEDIA quota/storage approval")
    source_control = mimic.get("source_preflight_control")
    if not isinstance(source_control, dict) or not source_control.get("path"):
        raise ValueError("MIMIC scoring requires a committed preperformance source-control receipt")
    control_path = (repo / source_control["path"]).resolve()
    if (not control_path.is_relative_to(repo)
            or sha256_file(control_path) != source_control.get("sha256")):
        raise ValueError("MIMIC source-control receipt hash is missing or mismatched")
    relative_control_path = control_path.relative_to(repo).as_posix()
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_control_path],
        cwd=repo, check=True, capture_output=True, text=True,
    )
    control = json.loads(control_path.read_text(encoding="utf-8"))
    preperformance = control.get("preperformance_controls", {})
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", control["protocol_commit"], commit],
            cwd=repo, check=True, capture_output=True, text=True,
        )
    except (KeyError, subprocess.CalledProcessError) as exc:
        raise ValueError("MIMIC source-control commit is not an ancestor of the scoring commit") from exc
    if (control.get("schema") != "TITAN_V45_MIMIC_PAC_SOURCE_PREFLIGHT_V1"
            or preperformance.get("waveform_inference_performed") is not False
            or preperformance.get("model_performance_metrics_computed") is not False
            or preperformance.get("machine_reports_used_as_clinical_labels") is not False
            or control.get("implementation_sha256") != config.get("implementation_sha256", {})):
        raise ValueError("MIMIC source-control receipt does not match the frozen no-performance preflight")
    integrity = verify_mimic_sha256_manifest(source)
    if integrity["source_manifest_sha256"] != control["source_integrity"]["source_manifest_sha256"]:
        raise ValueError("MIMIC source differs from the audited preperformance source")

    logistic, mlp = _load_probe_bundle(
        model_bundle, args.expected_model_bundle_sha256,
        commit=commit, config_hash=config_hash, model_sha256=config["model"]["sha256"],
    )
    checkpoint = release / config["model"]["backbone"]
    if sha256_file(checkpoint) != config["model"]["sha256"]:
        raise ValueError("frozen V3F checkpoint SHA-256 mismatch")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for frozen V3F MIMIC scoring")
    device_name = torch.cuda.get_device_name()
    if config["inference"]["device_contains"] not in device_name:
        raise ValueError("MIMIC scoring must use the frozen A100 environment")
    inference = config["inference"]
    torch.manual_seed(inference["seed"])
    torch.cuda.manual_seed_all(inference["seed"])
    torch.use_deterministic_algorithms(inference["deterministic_algorithms"])
    torch.backends.cudnn.deterministic = inference["cudnn_deterministic"]
    torch.backends.cudnn.benchmark = inference["cudnn_benchmark"]
    torch.backends.cuda.matmul.allow_tf32 = inference["tf32"]
    torch.backends.cudnn.allow_tf32 = inference["tf32"]
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != inference["cublas_workspace_config"]:
        raise ValueError("CUBLAS_WORKSPACE_CONFIG differs from the frozen protocol")

    states, patients, hashes, statuses = [], [], [], []
    scores = {"weighted_l2_logistic": [], "fixed_mlp_sensitivity": []}
    amplitudes = []
    pending = []
    pending_windows = 0
    source_control_total = int(
        control["denominators"]["paired_record_list_and_machine_report_rows"]
    )
    batch_size = args.batch_windows
    with V3FTokenEmbeddingExtractor(
        checkpoint, expected_sha256=config["model"]["sha256"], device="cuda"
    ) as extractor:
        for row in iter_mimic_machine_reports(
            source / "machine_measurements.csv", source / "record_list.csv"
        ):
            index = len(states)
            state = row["report_state"]
            states.append(state)
            patients.append(row["subject_id"])
            hashes.append("")
            statuses.append("")
            for values in scores.values():
                values.append(float("nan"))
            try:
                record_base = resolve_mimic_record_base(source, row["record_path"])
                prepared = prepare_mimic_waveform(record_base, wfdb_module=wfdb)
            except (OSError, RuntimeError, ValueError) as exc:
                statuses[index] = f"failure:{_failure_reason(exc)}"
                continue
            statuses[index] = "scored"
            hashes[index] = prepared["signal_sha256"]
            amplitudes.append(prepared["max_abs_mv"])
            pending.append((index, prepared))
            pending_windows += len(prepared["windows"])
            if pending_windows >= batch_size:
                _flush(pending, extractor, logistic, mlp, batch_size, scores)
                pending, pending_windows = [], 0
        if pending:
            _flush(pending, extractor, logistic, mlp, batch_size, scores)

    if len(states) != source_control_total:
        raise ValueError("MIMIC scoring denominator differs from the committed source audit")
    threshold = float(config["metrics"]["threshold"])
    interval = config["metrics"]["intervals"]
    reports = {
        name: summarize_mimic_pac_concordance(
            states, model_scores, patients, hashes, statuses,
            threshold=threshold, ece_bins=config["metrics"]["ece_bins"],
            replicates=interval["replicates"], seed=interval["seed"],
        )
        for name, model_scores in scores.items()
    }
    aggregate = {
        "schema": "TITAN_V45_MIMIC_PAC_MACHINE_REPORT_AGGREGATE_V1",
        "status": "exploratory_automatic_report_concordance",
        "reference_scope": "machine-generated report mention only; not clinical accuracy",
        "protocol_commit": commit,
        "protocol_config_sha256": config_hash,
        "source_manifest_sha256": integrity["source_manifest_sha256"],
        "source_record_count": len(states),
        "models": reports,
        "physical_amplitude_millivolt_per_waveform_max_abs_quantiles": {
            "p50": float(np.quantile(amplitudes, 0.50)) if amplitudes else None,
            "p95": float(np.quantile(amplitudes, 0.95)) if amplitudes else None,
            "p99": float(np.quantile(amplitudes, 0.99)) if amplitudes else None,
            "p999": float(np.quantile(amplitudes, 0.999)) if amplitudes else None,
        },
        "privacy": {
            "subject_or_study_identifiers_exported": False,
            "waveform_hashes_exported": False,
            "row_level_scores_exported": False,
            "report_text_exported": False,
        },
    }
    receipt = {
        "schema": "TITAN_V45_MIMIC_PAC_MACHINE_REPORT_RECEIPT_V1",
        "protocol_commit": commit,
        "protocol_config_sha256": config_hash,
        "source_control_receipt_sha256": source_control["sha256"],
        "source_integrity": integrity,
        "model_bundle_sha256": args.expected_model_bundle_sha256,
        "v3f_checkpoint_sha256": config["model"]["sha256"],
        "implementation_sha256": config.get("implementation_sha256", {}),
        "dependency_archive_sha256": dependency_hashes,
        "aggregate_sha256": sha256_file(aggregate_path) if aggregate_path.exists() else None,
        "metrics_are_machine_report_concordance_only": True,
        "backbone_pretraining_independence_certified": False,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "runtime": {
            **runtime_versions, "device": device_name,
        },
    }
    _write_exclusive(aggregate_path, aggregate)
    receipt["aggregate_sha256"] = sha256_file(aggregate_path)
    _write_exclusive(receipt_path, receipt)
    return aggregate, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--private-model-bundle", type=Path, required=True)
    parser.add_argument("--expected-model-bundle-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--batch-windows", type=int, default=512)
    args = parser.parse_args()
    if args.batch_windows < 1:
        parser.error("--batch-windows must be positive")
    aggregate, receipt = run(args)
    print(json.dumps({
        "source_record_count": aggregate["source_record_count"],
        "models": {
            name: value["scored_binary_report_records"]
            for name, value in aggregate["models"].items()
        },
        "receipt_sha256": sha256_file(args.output_dir / "mimic_pac_machine_report_receipt.json"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
