"""Fit fixed PAC probes on SPH training patients and report the exploratory holdout."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.sph import read_sph_dictionary, read_sph_metadata
from titan_v45.evaluation.pac_probe import (
    binary_metrics,
    duplicate_balanced_sample_weights,
    fit_logistic_probe,
    fit_mlp_probe,
    patient_cluster_bootstrap,
    patient_component_ids,
    patient_group_split,
    predict_logistic_probe,
    predict_mlp_probe,
)
from titan_v45.evaluation.provenance import (
    read_required_sha256_environment,
    verify_implementation_sha256,
    verify_runtime_versions,
)
from titan_v45.models.v3f_embeddings import sha256_file

CONFIG_RELATIVE = "configs/external_validation/pac_v3f_embedding_probe.json"
METRICS = ("accuracy", "sensitivity", "specificity", "precision", "recall", "f1",
           "auroc", "average_precision", "brier_score", "ece")


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


def _write_json_exclusive(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _metric_package(labels, scores, components, *, seed, replicates):
    point = binary_metrics(labels, scores, threshold=0.5, ece_bins=10)
    bootstrap = patient_cluster_bootstrap(
        labels, scores, components, replicates=replicates, seed=seed
    )
    return {"point_estimates": point, "patient_cluster_bootstrap": bootstrap}


def run(args):
    repo = args.repo.resolve()
    source = args.source.resolve()
    embeddings_path = args.embeddings.resolve()
    embedding_receipt_path = args.embedding_receipt.resolve()
    private_bundle_path = args.private_model_bundle.resolve()
    public_dir = args.public_dir.resolve()
    if source.is_relative_to(repo) or embeddings_path.is_relative_to(repo):
        raise ValueError("SPH source and private embeddings must stay outside Git")
    if embedding_receipt_path.is_relative_to(repo) or private_bundle_path.is_relative_to(repo):
        raise ValueError("embedding receipt and fitted model bundle must stay outside Git")
    if not public_dir.is_relative_to(repo):
        raise ValueError("aggregate report must be written inside the repository")
    aggregate_path = public_dir / "pac_probe_aggregate.json"
    receipt_path = public_dir / "pac_probe_receipt.json"
    if aggregate_path.exists() or receipt_path.exists() or private_bundle_path.exists():
        raise FileExistsError("PAC probe aggregate, receipt or private model already exists")

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
    }, {name: config["environment"]["versions"][name]
        for name in ("python", "torch", "cuda", "numpy", "scipy")})
    for name, expected in config["source"]["sha256"].items():
        if sha256_file(source / name) != expected:
            raise ValueError(f"SPH source hash mismatch: {name}")
    for name, control in config["preperformance_controls"].items():
        path = (repo / control["path"]).resolve()
        if not path.is_relative_to(repo) or sha256_file(path) != control["sha256"]:
            raise ValueError(f"pre-performance control hash mismatch: {name}")
        if (name == "retained_source_signature_audit"
                and json.loads(path.read_text(encoding="utf-8")).get("independence_certified")
                is not False):
            raise ValueError("historical source independence must remain uncertified")
    embedding_receipt = json.loads(embedding_receipt_path.read_text(encoding="utf-8"))
    if (embedding_receipt.get("protocol_commit") != commit
            or embedding_receipt.get("protocol_config_sha256") != config_hash
            or embedding_receipt.get("v3f_checkpoint_sha256") != config["model"]["sha256"]
            or embedding_receipt.get("embedding_archive_sha256") != sha256_file(embeddings_path)
            or embedding_receipt.get("labels_read_or_used") is not False):
        raise ValueError("label-blind embedding receipt does not match frozen protocol inputs")

    primary, modifier = read_sph_dictionary(
        (source / "code.csv").read_text(encoding="utf-8-sig")
    )
    metadata = read_sph_metadata(
        (source / "metadata.csv").read_text(encoding="utf-8-sig"), primary, modifier
    )
    if len(metadata) != config["source"]["expected_records"]:
        raise ValueError("SPH label metadata count differs from protocol")

    with np.load(embeddings_path, allow_pickle=False) as archive:
        record_ids = archive["record_id"].astype(str)
        signal_hashes = archive["signal_sha256"].astype(str)
        features = archive["features"].astype(np.float32, copy=True)
        window_counts = archive["window_count"].astype(np.int64)
    if (record_ids.ndim != 1 or len(set(record_ids)) != len(record_ids)
            or signal_hashes.shape != record_ids.shape or window_counts.shape != record_ids.shape
            or features.shape != (len(record_ids), 1280) or not np.isfinite(features).all()
            or any(record not in metadata for record in record_ids)):
        raise ValueError("private embedding archive does not reconcile to SPH label metadata")

    patient_ids = np.asarray([metadata[record].patient for record in record_ids], dtype=str)
    target_code = int(config["source"]["label"]["positive_primary_code"])
    labels = np.asarray([target_code in metadata[record].primary_codes for record in record_ids],
                        dtype=np.int8)
    components = patient_component_ids(patient_ids, signal_hashes)
    train_index, holdout_index = patient_group_split(
        patient_ids,
        labels,
        signal_hashes=signal_hashes,
        train_fraction=config["split"]["train_fraction"],
        seed=config["split"]["seed"],
    )
    if set(components[train_index]) & set(components[holdout_index]):
        raise RuntimeError("patient or exact-waveform component crosses the frozen split")
    weights = duplicate_balanced_sample_weights(labels[train_index], signal_hashes[train_index])
    model_config = config["probes"]
    logistic = fit_logistic_probe(
        features[train_index], labels[train_index], weights,
        c=model_config["baseline"]["c"],
        max_iter=model_config["baseline"]["max_iterations"],
    )
    mlp_config = model_config["sensitivity"]
    mlp = fit_mlp_probe(
        features[train_index], labels[train_index], weights,
        seed=mlp_config["seed"], epochs=mlp_config["epochs"],
        batch_size=mlp_config["batch_size"], learning_rate=mlp_config["learning_rate"],
        weight_decay=mlp_config["weight_decay"], dropout=mlp_config["dropout"],
    )
    predictions = {
        "weighted_l2_logistic": predict_logistic_probe(features[holdout_index], logistic),
        "fixed_mlp_sensitivity": predict_mlp_probe(features[holdout_index], mlp),
    }
    holdout_y = labels[holdout_index]
    holdout_components = components[holdout_index]

    labels_by_hash = defaultdict(set)
    patients_by_hash = defaultdict(set)
    for digest, label, patient in zip(signal_hashes, labels, patient_ids, strict=True):
        labels_by_hash[digest].add(int(label))
        patients_by_hash[digest].add(patient)
    discordant_hashes = {digest for digest, values in labels_by_hash.items() if len(values) > 1}
    hash_counts = Counter(signal_hashes.tolist())
    duplicate_groups = {digest: values for digest, values in labels_by_hash.items()
                        if hash_counts[digest] > 1}
    cross_patient_duplicate_groups = sum(
        len(patients_by_hash[digest]) > 1 for digest in duplicate_groups
    )
    duplicate_config = config["duplicate_policy"]
    if (len(duplicate_groups) != duplicate_config["expected_exact_duplicate_groups"]
            or cross_patient_duplicate_groups != duplicate_config["expected_cross_patient_exact_groups"]
            or len(discordant_hashes) != duplicate_config["expected_pac_discordant_exact_groups"]):
        raise ValueError("private embedding duplicate groups differ from the frozen audit")
    sensitivity_mask = np.asarray(
        [digest not in discordant_hashes for digest in signal_hashes[holdout_index]], dtype=bool
    )
    reports = {}
    for name, probabilities in predictions.items():
        primary_report = _metric_package(
            holdout_y, probabilities, holdout_components,
            seed=config["metrics"]["intervals"]["seed"],
            replicates=config["metrics"]["intervals"]["replicates"],
        )
        if sensitivity_mask.any():
            duplicate_sensitivity = _metric_package(
                holdout_y[sensitivity_mask], probabilities[sensitivity_mask],
                holdout_components[sensitivity_mask],
                seed=config["metrics"]["intervals"]["seed"],
                replicates=config["metrics"]["intervals"]["replicates"],
            )
        else:
            duplicate_sensitivity = {"status": "not_estimable_no_holdout_rows_after_exclusion"}
        reports[name] = {
            "holdout": primary_report,
            "holdout_without_pac_discordant_exact_duplicate_groups": duplicate_sensitivity,
        }

    split_hash = hashlib.sha256()
    train_index_set = set(train_index.tolist())
    for record, index in sorted((record, int(index)) for index, record in enumerate(record_ids)):
        split_hash.update(record.encode("ascii"))
        split_hash.update(b"\0train\0" if index in train_index_set
                          else b"\0holdout\0")
    private_bundle = {
        "schema": "TITAN_V45_PAC_PROBE_MODEL_BUNDLE_PRIVATE_V1",
        "protocol_commit": commit,
        "protocol_config_sha256": config_hash,
        "v3f_checkpoint_sha256": config["model"]["sha256"],
        "logistic": {
            "mean": torch.as_tensor(logistic["mean"]),
            "scale": torch.as_tensor(logistic["scale"]),
            "coefficient": torch.as_tensor(logistic["coefficient"]),
            "intercept": logistic["intercept"],
            "c": logistic["c"],
        },
        "mlp": {
            "mean": torch.as_tensor(mlp["mean"]),
            "scale": torch.as_tensor(mlp["scale"]),
            "state_dict": mlp["state_dict"],
            "input_dim": mlp["input_dim"],
            "seed": mlp["seed"],
            "epochs": mlp["epochs"],
            "batch_size": mlp["batch_size"],
            "learning_rate": mlp["learning_rate"],
            "weight_decay": mlp["weight_decay"],
            "dropout": mlp["dropout"],
        },
    }
    private_bundle_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if private_bundle_path.parent.stat().st_mode & 0o077:
        raise PermissionError("private model directory must have mode 700")
    torch.save(private_bundle, private_bundle_path)

    public_aggregate = {
        "schema": "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V1",
        "status": "exploratory_patient_split_holdout",
        "target": "SPH primary code 30; code 31 excluded; ECG statement, not clinical adjudication",
        "source": {
            "metadata_records": len(metadata),
            "embedding_eligible_records": len(record_ids),
            "embedding_rows": len(record_ids),
            "unique_source_patients_in_eligible_rows": int(len(set(patient_ids))),
            "technical_status_counts": embedding_receipt["status_counts"],
            "window_count_total": int(window_counts.sum()),
        },
        "split": {
            "train_records": int(len(train_index)),
            "holdout_records": int(len(holdout_index)),
            "train_patient_count": int(len(set(components[train_index]))),
            "holdout_patient_count": int(len(set(components[holdout_index]))),
            "train_positive": int(labels[train_index].sum()),
            "train_negative": int(len(train_index) - labels[train_index].sum()),
            "holdout_positive": int(holdout_y.sum()),
            "holdout_negative": int(len(holdout_y) - holdout_y.sum()),
            "seed": config["split"]["seed"],
            "train_fraction": config["split"]["train_fraction"],
            "private_split_assignment_sha256": split_hash.hexdigest(),
        },
        "duplicate_audit": {
            "exact_duplicate_groups": len(duplicate_groups),
            "cross_patient_exact_duplicate_groups": cross_patient_duplicate_groups,
            "groups_with_pac_label_conflict": len(discordant_hashes),
            "holdout_rows_excluded_in_sensitivity": int((~sensitivity_mask).sum()),
            "duplicate_training_weighting": config["duplicate_policy"]["training_weight"],
        },
        "models": reports,
        "limitations": [
            "SPH report-level PAC labels are not clinical adjudication.",
            "The holdout is exploratory and is not independent external validation.",
            "The previously published SPH Primary8 PAC result was already observed.",
            "V3F historical training-source overlap is not certified.",
        ],
        "patient_or_record_identifiers_present": False,
        "row_level_predictions_present": False,
        "probe_weights_present": False,
    }
    public_dir.mkdir(parents=True, exist_ok=True)
    _write_json_exclusive(aggregate_path, public_aggregate)
    receipt = {
        "schema": "TITAN_V45_SPH_PAC_PROBE_RECEIPT_V1",
        "protocol_commit": commit,
        "protocol_config_sha256": config_hash,
        "source_sha256": config["source"]["sha256"],
        "v3f_checkpoint_sha256": config["model"]["sha256"],
        "embedding_archive_sha256": sha256_file(embeddings_path),
        "embedding_receipt_sha256": sha256_file(embedding_receipt_path),
        "dependency_archive_sha256": dependency_hashes,
        "runtime": runtime_versions,
        "private_model_bundle_sha256": sha256_file(private_bundle_path),
        "public_aggregate_sha256": sha256_file(aggregate_path),
        "labels_used_for_head_fitting": True,
        "threshold_or_model_tuning_on_holdout": False,
        "mimic_data_consulted": False,
        "row_level_data_in_repository": False,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    _write_json_exclusive(receipt_path, receipt)
    return {"aggregate": public_aggregate, "receipt": receipt}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--embedding-receipt", type=Path, required=True)
    parser.add_argument("--private-model-bundle", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, default=ROOT / "outputs/results/external_sph_pac")
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({"holdout_records": result["aggregate"]["split"]["holdout_records"],
                      "models": list(result["aggregate"]["models"]),
                      "aggregate_sha256": result["receipt"]["public_aggregate_sha256"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
