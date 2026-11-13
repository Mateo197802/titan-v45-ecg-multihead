"""Label-blind perturbation audit of frozen SPH inference; aggregate output only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import subprocess
import sys
from pathlib import Path

SELECTION_NAMESPACE = "TITAN-V46-SPH-SCALE-V1:"
SAMPLE_SIZE = 128
FACTORS = (0.5, 1.0, 2.0)
FROZEN_COMMIT = "eb1c67b9229af875a9f868797b0c2f5c546e3dac"
FROZEN_PROTOCOL_SHA = "d788ad8cca94793cebb738496acc131e82b1ca1900976f11020b99a79a5fc366"
FROZEN_LEDGER_SHA = "4a3a1e61b1784e06190d5caaa089fca04ef84792acb3a5f9fc1af3f9c1173462"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_within(path, root):
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def select_records(records, count=SAMPLE_SIZE):
    records = list(records)
    if len(set(records)) != len(records) or count < 1 or count > len(records):
        raise ValueError("invalid sample population")
    return tuple(sorted(records, key=lambda item: (
        hashlib.sha256((SELECTION_NAMESPACE + item).encode("utf-8")).digest(), item))[:count])


def compare(reference, candidate):
    if not reference or len(reference) != len(candidate):
        raise ValueError("paired sample sizes do not match")
    result = {"records": len(reference), "profiles": {}}
    for profile in ("P6", "P8", "P4"):
        scores = {}
        first = reference[0]["profiles"][profile]["scores"]
        for name in first:
            changes, flipped = [], 0
            for before, after in zip(reference, candidate, strict=True):
                if before["status"] != "scored" or after["status"] != "scored":
                    raise ValueError("sample inference failed")
                old, new = before["profiles"][profile], after["profiles"][profile]
                if set(old["scores"]) != set(first) or set(new["scores"]) != set(first):
                    raise ValueError("score class contract changed")
                x, y = float(old["scores"][name]), float(new["scores"][name])
                if not math.isfinite(x) or not math.isfinite(y) or not 0 <= x <= 1 or not 0 <= y <= 1:
                    raise ValueError("invalid model score")
                changes.append(abs(x - y))
                flipped += (name in old["labels"]) != (name in new["labels"])
            scores[name] = {"mean_absolute": sum(changes) / len(changes),
                            "max_absolute": max(changes), "label_changes": flipped}
        old_rows = [row["profiles"][profile] for row in reference]
        new_rows = [row["profiles"][profile] for row in candidate]
        result["profiles"][profile] = {
            "score_changes": scores,
            "top1_changes": sum(x["top1"] != y["top1"] for x, y in zip(old_rows, new_rows, strict=True)),
            "fallback_changes": sum(x["used_fallback"] != y["used_fallback"]
                                    for x, y in zip(old_rows, new_rows, strict=True)),
        }
    return result


def run(args):
    repo, source, release = args.frozen_repo.resolve(), args.source.resolve(), args.release.resolve()
    output = args.output.resolve()
    experiment_repo = Path(__file__).resolve().parents[2]
    private_paths = (source, args.ledger.resolve(), output)
    if any(is_within(path, repo) or is_within(path, experiment_repo)
           for path in private_paths):
        raise ValueError("source, ledger, and output must remain outside both Git checkouts")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                            capture_output=True, text=True).stdout.strip()
    clean = subprocess.run(["git", "status", "--porcelain"], cwd=repo, check=True,
                           capture_output=True, text=True).stdout.strip()
    config = repo / "configs/external_validation/sph_frozen.json"
    if commit != FROZEN_COMMIT or clean or sha256(config) != FROZEN_PROTOCOL_SHA:
        raise ValueError("frozen SPH source does not match preregistered tree")
    experiment_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=experiment_repo, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if subprocess.run(["git", "status", "--porcelain"], cwd=experiment_repo, check=True,
                      capture_output=True, text=True).stdout.strip():
        raise ValueError("BenchmarkMax experiment checkout must be clean")
    protocol = json.loads(config.read_text(encoding="utf-8"))
    for name, digest in protocol["source_sha256"].items():
        if sha256(source / name) != digest:
            raise ValueError(f"source hash mismatch: {name}")
    if sha256(args.ledger) != FROZEN_LEDGER_SHA:
        raise ValueError("frozen ledger hash mismatch")
    for name, digest in protocol["implementation_sha256"].items():
        if sha256(repo / name) != digest:
            raise ValueError(f"implementation hash mismatch: {name}")
    sys.path.insert(0, str(repo / "src"))
    spec = importlib.util.spec_from_file_location("frozen_sph_scorer", repo / "scripts/external_validation/score_sph_frozen.py")
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    import h5py
    import numpy as np
    import scipy
    import torch
    import wfdb
    import zstandard

    actual_versions = {
        "python": platform.python_version(), "torch": torch.__version__,
        "cuda": torch.version.cuda, "numpy": np.__version__, "scipy": scipy.__version__,
        "h5py": h5py.__version__, "wfdb": wfdb.__version__,
        "zstandard": zstandard.__version__,
    }
    if actual_versions != protocol["environment"]["versions"]:
        raise ValueError(f"runtime versions differ from frozen protocol: {actual_versions}")
    if not torch.cuda.is_available() or os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise ValueError("expected CUDA and deterministic cuBLAS settings")
    if protocol["environment"]["device_contains"] not in torch.cuda.get_device_name():
        raise ValueError("GPU differs from frozen SPH inference")
    torch.manual_seed(protocol["inference"]["seed"])
    torch.cuda.manual_seed_all(protocol["inference"]["seed"])
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(2)
    contract = json.loads((repo / "outputs/models/heads/global_head_contracts.json").read_text())
    names = {scorer.P4_BACKBONE, scorer.P4_SPECIALIST, scorer.RHYTHM_BACKBONE, *scorer.HEADS.values()}
    assets, model_hashes = scorer.verified_assets(repo, release, names)
    if model_hashes != protocol["model_sha256"]:
        raise ValueError("checkpoint hash mismatch")
    morphology = scorer._load_morphology(repo)
    event = scorer.load_recorded_event_extractor(repo / "docs/provenance/recovered-original-sources-20261029.zip")
    rhythm = scorer.FrozenRhythm(assets, contract, event, "cuda")
    pathology = scorer.FrozenPathology(assets, contract, "cuda")
    if {key: float(value) for key, value in pathology.thresholds.items()} != protocol["thresholds"]["P4"]:
        raise ValueError("checkpoint threshold mismatch")
    index = scorer._read_signal_index(source / "metadata.csv")
    if len(index) != protocol["expected_source_records"]:
        raise ValueError("source population size mismatch")
    selected = select_records(index)
    selected_set = set(selected)
    archived = {}
    with args.ledger.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["record_id"] in selected_set:
                if row["record_id"] in archived:
                    raise ValueError("duplicate selected ledger record")
                archived[row["record_id"]] = row
    if set(archived) != selected_set:
        raise ValueError("selected records missing from archived ledger")
    outputs = {factor: {} for factor in FACTORS}
    pending = {factor: [] for factor in FACTORS}

    def flush(factor):
        if not pending[factor]:
            return
        writer = io.StringIO()
        scorer._score_batch(pending[factor], rhythm, pathology, protocol["thresholds"], writer)
        for line in writer.getvalue().splitlines():
            row = json.loads(line)
            if row["status"] != "scored" or row["record_id"] in outputs[factor]:
                raise ValueError("selected sample inference failure or duplicate")
            outputs[factor][row["record_id"]] = row
        pending[factor].clear()

    found = set()
    for record, content in scorer.open_sph_records(source / "records.tar.gz"):
        if record not in selected_set:
            continue
        if record in found:
            raise ValueError("duplicate selected waveform")
        found.add(record)
        signal, _ = scorer.read_sph_signal(content, index[record])
        for factor in FACTORS:
            scaled = signal.astype(np.float64) * factor
            rhythm_windows = scorer.prepare_sph_waveform(scaled, morphology, branch="rhythm")
            pathology_window = scorer.prepare_sph_waveform(scaled, morphology, branch="P4")[0]
            pending[factor].append({"record_id": record, "rhythm_samples": rhythm_windows,
                                    "pathology_sample": pathology_window})
            if len(pending[factor]) == 8:
                flush(factor)
    for factor in FACTORS:
        flush(factor)
        if set(outputs[factor]) != selected_set or found != selected_set:
            raise ValueError("not every selected waveform was scored")
    baseline = [outputs[1.0][item] for item in selected]
    report = {
        "schema": "TITAN_V46_SPH_AMPLITUDE_SENSITIVITY_V1",
        "scope": "Exploratory label-blind signal-scale perturbation, not clinical performance or unit certification.",
        "experiment_commit": experiment_commit,
        "selected_records": len(selected), "factors": list(FACTORS),
        "baseline_replay_vs_archived": compare([archived[item] for item in selected], baseline),
        "perturbations_vs_factor_1": {str(factor): compare(baseline, [outputs[factor][item] for item in selected])
                                      for factor in (0.5, 2.0)},
        "individual_records_exported": False, "labels_used_for_selection_or_inference": False,
        "model_sha256": model_hashes, "frozen_protocol_sha256": FROZEN_PROTOCOL_SHA,
        "frozen_ledger_sha256": FROZEN_LEDGER_SHA, "script_sha256": sha256(__file__),
        "job_id": os.environ.get("SLURM_JOB_ID", "not_slurm"),
        "gpu": torch.cuda.get_device_name(),
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    os.chmod(output, 0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("frozen-repo", "source", "release", "ledger", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
