"""Extract private, label-blind V3F token embeddings for the frozen SPH PAC probe."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import scipy
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.sph import open_sph_records, read_sph_signal
from titan_v45.data.sph_waveform import prepare_sph_waveform
from titan_v45.evaluation.pac_probe import pool_record_windows, pool_v3f_tokens
from titan_v45.evaluation.provenance import (
    read_required_sha256_environment,
    verify_implementation_sha256,
    verify_runtime_versions,
)
from titan_v45.models.v3f_embeddings import V3FTokenEmbeddingExtractor, sha256_file

CONFIG_RELATIVE = "configs/external_validation/pac_v3f_embedding_probe.json"


def _read_signal_index(path):
    records = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"ECG_ID", "N"}.issubset(reader.fieldnames or ()):
            raise ValueError("SPH metadata lacks ECG_ID or N")
        for row in reader:
            record, samples = row["ECG_ID"], int(row["N"])
            if not record or samples <= 0 or record in records:
                raise ValueError("invalid or duplicate SPH metadata row")
            records[record] = samples
    return records


def _verify_frozen_tree(repo, expected_commit, expected_config_sha256):
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


def _zero_morphology(_signal, *, fs):
    if fs != 125:
        raise ValueError("unexpected morphology sampling rate")
    return np.zeros(10, dtype=np.float32)


def _reason(exc):
    message = str(exc).lower()
    if "duration" in message:
        return "unsupported_duration"
    if "nonfinite" in message or "finite" in message:
        return "nonfinite_signal_or_feature"
    if "flat" in message or "standard deviation" in message:
        return "flat_or_low_variance_signal"
    if "hdf5" in message or "signal shape" in message or "dtype" in message:
        return "invalid_hdf5_or_signal_contract"
    if "lead" in message:
        return "unrecognized_leads"
    return "waveform_preprocessing_failure"


def _flush(records, extractor, window_batch_size, features, identities, window_counts):
    if not records:
        return
    flattened = [sample for _record, samples, _digest in records for sample in samples]
    tokens = extractor.extract_windows(flattened, batch_size=window_batch_size)
    window_embeddings = pool_v3f_tokens(tokens)
    cursor = 0
    for record, samples, digest in records:
        count = len(samples)
        features.append(pool_record_windows(window_embeddings[cursor:cursor + count]))
        identities.append((record, digest))
        window_counts.append(count)
        cursor += count
    if cursor != len(window_embeddings):
        raise RuntimeError("window embedding accounting mismatch")


def run(args):
    import h5py

    repo = args.repo.resolve()
    source = args.source.resolve()
    release = args.release_root.resolve()
    output = args.output.resolve()
    receipt_path = args.receipt.resolve()
    if source.is_relative_to(repo) or output.is_relative_to(repo) or receipt_path.is_relative_to(repo):
        raise ValueError("source, embeddings and receipt must stay outside Git")
    if output == receipt_path or output.exists() or receipt_path.exists():
        raise FileExistsError("private output or receipt already exists")

    config, config_hash, commit = _verify_frozen_tree(
        repo, args.expected_commit, args.expected_config_sha256
    )
    dependency_hashes = read_required_sha256_environment({
        "python_deps": "TITAN_PYTHON_DEPS_SHA256",
        "h5py_deps": "TITAN_H5PY_DEPS_SHA256",
    }, expected_hashes=config["environment"]["dependency_archive_sha256"])
    runtime_versions = verify_runtime_versions({
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "h5py": h5py.__version__,
    }, {name: config["environment"]["versions"][name]
        for name in ("python", "torch", "cuda", "numpy", "scipy", "h5py")})
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
    model_path = release / config["model"]["backbone"]
    if sha256_file(model_path) != config["model"]["sha256"]:
        raise ValueError("frozen V3F checkpoint hash mismatch")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for frozen V3F embedding extraction")
    device = torch.cuda.get_device_name()
    inference = config["inference"]
    if inference["device_contains"] not in device:
        raise ValueError("embedding extraction must use the frozen A100 environment")
    torch.manual_seed(inference["seed"])
    torch.cuda.manual_seed_all(inference["seed"])
    torch.use_deterministic_algorithms(inference["deterministic_algorithms"])
    torch.backends.cudnn.deterministic = inference["cudnn_deterministic"]
    torch.backends.cudnn.benchmark = inference["cudnn_benchmark"]
    torch.backends.cuda.matmul.allow_tf32 = inference["tf32"]
    torch.backends.cudnn.allow_tf32 = inference["tf32"]
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != inference["cublas_workspace_config"]:
        raise ValueError("CUBLAS_WORKSPACE_CONFIG differs from the frozen protocol")

    metadata = _read_signal_index(source / "metadata.csv")
    if len(metadata) != config["source"]["expected_records"]:
        raise ValueError("SPH metadata row count differs from the frozen protocol")

    for parent in {output.parent, receipt_path.parent}:
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if parent.stat().st_mode & 0o077:
            raise PermissionError("private output directory must have mode 700")
    previous_umask = os.umask(0o077)
    features, identities, window_counts = [], [], []
    status_counts = Counter()
    seen = set()
    pending = []
    pending_windows = 0
    batch_windows = args.batch_windows

    try:
        with V3FTokenEmbeddingExtractor(
            model_path, expected_sha256=config["model"]["sha256"], device="cuda"
        ) as extractor:
            for record, content in open_sph_records(source / "records.tar.gz"):
                if record in seen:
                    raise ValueError("duplicate SPH ECG ID in signal archive")
                seen.add(record)
                if record not in metadata:
                    status_counts["archive_record_without_metadata"] += 1
                    continue
                try:
                    signal, _dtype = read_sph_signal(content, metadata[record])
                    digest = hashlib.sha256(
                        signal.astype("<f8", copy=False).tobytes()
                    ).hexdigest()
                    samples = prepare_sph_waveform(
                        signal, _zero_morphology, branch="rhythm"
                    )
                except (OSError, ValueError) as exc:
                    status_counts[_reason(exc)] += 1
                    continue
                pending.append((record, samples, digest))
                pending_windows += len(samples)
                if pending_windows >= batch_windows:
                    _flush(pending, extractor, batch_windows, features, identities, window_counts)
                    pending, pending_windows = [], 0
                status_counts["embedded"] += 1
            if pending:
                _flush(pending, extractor, batch_windows, features, identities, window_counts)
    finally:
        os.umask(previous_umask)

    missing = len(metadata.keys() - seen)
    if missing:
        status_counts["metadata_without_archive_member"] += missing
    if len(features) + sum(value for key, value in status_counts.items()
                           if key not in {"embedded", "archive_record_without_metadata"}) != len(metadata):
        raise RuntimeError("SPH embedding flow does not reconcile to metadata denominator")
    if not features:
        raise RuntimeError("no eligible SPH waveform produced a V3F embedding")

    identities = np.asarray(identities, dtype=str)
    matrix = np.stack(features).astype(np.float32, copy=False)
    if matrix.shape != (len(identities), 1280):
        raise RuntimeError("unexpected pooled V3F embedding matrix shape")
    with output.open("xb") as stream:
        np.savez_compressed(
            stream,
            record_id=identities[:, 0],
            signal_sha256=identities[:, 1],
            features=matrix,
            window_count=np.asarray(window_counts, dtype=np.int16),
        )
    receipt = {
        "schema": "TITAN_V45_SPH_PAC_V3F_EMBEDDING_RECEIPT_V1",
        "protocol_commit": commit,
        "protocol_config_sha256": config_hash,
        "source_sha256": config["source"]["sha256"],
        "preperformance_control_sha256": {
            name: control["sha256"] for name, control in config["preperformance_controls"].items()
        },
        "v3f_checkpoint_sha256": config["model"]["sha256"],
        "implementation_sha256": config.get("implementation_sha256", {}),
        "dependency_archive_sha256": dependency_hashes,
        "embedding_archive_sha256": sha256_file(output),
        "embedding_rows": int(len(matrix)),
        "embedding_shape": list(matrix.shape),
        "window_count_total": int(np.asarray(window_counts, dtype=np.int64).sum()),
        "metadata_records": int(len(metadata)),
        "archive_records": int(len(seen)),
        "status_counts": dict(sorted(status_counts.items())),
        "labels_read_or_used": False,
        "patient_or_record_identifiers_in_receipt": False,
        "runtime": {**runtime_versions, "device": device,
                    "deterministic_algorithms": inference["deterministic_algorithms"],
                    "tf32": inference["tf32"],
                    "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG")},
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--batch-windows", type=int, default=32)
    args = parser.parse_args()
    if args.batch_windows < 1:
        parser.error("--batch-windows must be positive")
    result = run(args)
    print(json.dumps({"embedding_rows": result["embedding_rows"],
                      "metadata_records": result["metadata_records"],
                      "status_counts": result["status_counts"],
                      "receipt_sha256": sha256_file(args.receipt)}, sort_keys=True))


if __name__ == "__main__":
    main()
