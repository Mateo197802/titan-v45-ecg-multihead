"""Extract private frozen-backbone features and immutable baseline scores."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.cascade.run_pathology import MORPHOLOGY_SHA  # noqa: E402
from titan_v45.data.reconstructed import prepare_p4_record, prepare_rhythm_record  # noqa: E402
from titan_v45.models.features import (  # noqa: E402
    compose_specialist_features,
    recovered_backbone_rhythm_probabilities,
)
from titan_v45.models.frozen_pathology import (  # noqa: E402
    BACKBONE as P4_BACKBONE,
)
from titan_v45.models.frozen_pathology import (
    SPECIALIST as P4_SPECIALIST,
)
from titan_v45.models.frozen_pathology import (
    FrozenPathology,
    verified_assets,
)
from titan_v45.models.frozen_rhythm import (  # noqa: E402
    BACKBONE as RHYTHM_BACKBONE,
)
from titan_v45.models.frozen_rhythm import (
    HEADS as RHYTHM_HEADS,
)
from titan_v45.models.frozen_rhythm import (
    TRAINER_SHA,
    FrozenRhythm,
    load_recorded_event_extractor,
)

CONFIG = ROOT / "configs/specialist_heads/study_20261111_v2.json"
EXPECTED_MORPHOLOGY_SHA = MORPHOLOGY_SHA
RHYTHM_BATCH_SIZE = 64
PATHOLOGY_BATCH_SIZE = 64


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_revision(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _safe_output(output: Path, data_root: Path) -> Path:
    output = output.resolve()
    root = data_root.resolve()
    if output == root or output.is_relative_to(root):
        raise ValueError("feature output must be outside the raw data cache")
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output, 0o700)
    return output


def _signal_path(source_root: Path, relative_base: str) -> Path:
    relative = Path(relative_base)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe relative record path")
    base = source_root / relative
    if not base.resolve().is_relative_to(source_root.resolve()):
        raise ValueError("record path escapes source root")
    for suffix in (".mat", ".dat"):
        signal = base.with_suffix(suffix)
        if signal.is_file() and not signal.is_symlink() and signal.resolve().is_relative_to(
            source_root.resolve()
        ):
            return signal
    raise FileNotFoundError("waveform signal is unavailable")


@torch.no_grad()
def _rhythm_batch(scorer: FrozenRhythm, samples: list[tuple[np.ndarray, np.ndarray, np.ndarray]]):
    device = scorer.device
    x, mask, morphology = (
        torch.as_tensor(np.stack(part), dtype=torch.float32, device=device)
        for part in zip(*samples, strict=True)
    )
    rhythm_logits, _, _, pathology_logits, backbone_features = scorer.model(
        x, morphology_features=morphology, lead_mask=mask, return_features=True
    )
    rhythm_probabilities = recovered_backbone_rhythm_probabilities(rhythm_logits)
    pathology_probabilities = pathology_logits.sigmoid()
    event_features = scorer.event_extractor(x)
    result = {}
    for profile, head in scorer.heads.items():
        features = compose_specialist_features(
            backbone_features=backbone_features,
            rhythm_probabilities=rhythm_probabilities,
            pathology_probabilities=pathology_probabilities,
            morphology=morphology,
            signal_event_features=event_features,
            layout=scorer.layouts[profile],
        )
        if features.shape[1] != 681:
            raise ValueError("released rhythm feature width does not match 681-input contract")
        logits = head(features).float()
        if profile in scorer.biases:
            logits = logits + scorer.biases[profile]
        result[profile] = (features.cpu().numpy(), logits.cpu().numpy())
    return result


@torch.no_grad()
def _pathology_batch(scorer: FrozenPathology, samples):
    x, mask, morphology = (
        torch.as_tensor(np.stack(part), dtype=torch.float32, device=scorer.device)
        for part in zip(*samples, strict=True)
    )
    rhythm_logits, _, _, pathology_logits, backbone_features = scorer.model(
        x, morphology_features=morphology, lead_mask=mask, return_features=True
    )
    features = compose_specialist_features(
        backbone_features=backbone_features,
        rhythm_probabilities=recovered_backbone_rhythm_probabilities(rhythm_logits),
        pathology_probabilities=pathology_logits.sigmoid(),
        morphology=morphology,
        layout=scorer.layout,
    )
    if features.shape[1] != 670:
        raise ValueError("released P4 feature width does not match 670-input contract")
    probabilities = scorer.head(features).sigmoid()
    return features.cpu().numpy(), probabilities.cpu().numpy()


def _safe_morphology(repo: Path):
    path = repo / "scripts/cedia/recovery_candidates/morphology_features_v4.py"
    if hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != EXPECTED_MORPHOLOGY_SHA:
        raise ValueError("candidate morphology implementation hash mismatch")
    spec = importlib.util.spec_from_file_location("specialist_pilot_morphology", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load hash-pinned morphology module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.normalized_morphology_features


def _atomic_npz(path: Path, **arrays: np.ndarray) -> None:
    with NamedTemporaryFile(mode="wb", dir=path.parent, suffix=".npz", delete=False) as temp:
        temp_path = Path(temp.name)
        np.savez_compressed(temp, **arrays)
        temp.flush()
        os.fsync(temp.fileno())
    os.chmod(temp_path, 0o600)
    temp_path.replace(path)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".json",
                            delete=False) as temp:
        temp_path = Path(temp.name)
        json.dump(payload, temp, sort_keys=True, indent=2)
        temp.write("\n")
        temp.flush()
        os.fsync(temp.fileno())
    os.chmod(temp_path, 0o600)
    temp_path.replace(path)


def run(data_root: Path, preflight_dir: Path, output_dir: Path, repo: Path, device: str,
        asset_root: Path | None = None):
    data_root, preflight_dir, repo = data_root.resolve(), preflight_dir.resolve(), repo.resolve()
    asset_root = (asset_root or repo).resolve()
    output_dir = _safe_output(output_dir, data_root)
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    preflight = json.loads((preflight_dir / "preflight_receipt.json").read_text(encoding="utf-8"))
    inventory_path = preflight_dir / "private_inventory.json"
    if preflight.get("schema") != "TITAN_SPECIALIST_INPUT_PREFLIGHT_V1":
        raise ValueError("unexpected preflight receipt schema")
    if preflight.get("study_id") != config["study_id"] or preflight.get("config_sha256") != _sha256(CONFIG):
        raise ValueError("preflight receipt does not match the frozen study configuration")
    if (preflight.get("fold10_used") is not False or preflight.get("sp_h_or_v3h_used") is not False
            or preflight.get("data_test_locked_or_manual_review_queue_used") is not False
            or preflight.get("performance_metrics_read_or_computed") is not False):
        raise ValueError("preflight receipt violates frozen data or outcome-blinding constraints")
    if _sha256(inventory_path) != preflight.get("private_inventory_sha256"):
        raise ValueError("private inventory hash does not match the preflight receipt")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if inventory.get("schema") != "TITAN_PRIVATE_SPECIALIST_INVENTORY_V1":
        raise ValueError("unexpected private inventory schema")
    contract = json.loads((repo / "outputs/models/heads/global_head_contracts.json").read_text(encoding="utf-8"))
    rhythm_names = {RHYTHM_BACKBONE, *RHYTHM_HEADS.values()}
    rhythm_assets, rhythm_hashes = verified_assets(repo, asset_root, rhythm_names)
    pathology_names = {P4_BACKBONE, P4_SPECIALIST}
    pathology_assets, pathology_hashes = verified_assets(repo, asset_root, pathology_names)
    morphology = _safe_morphology(repo)
    event_archive = repo / "docs/provenance/recovered-original-sources-20261029.zip"
    rhythm_scorer = FrozenRhythm(
        rhythm_assets, contract, load_recorded_event_extractor(event_archive), device
    )
    pathology_scorer = FrozenPathology(pathology_assets, contract, device)
    frozen_thresholds = _baseline_thresholds(repo, pathology_scorer)

    rows = inventory["rows"]
    rhythm_records, rhythm_lookup = [], {}
    for row in rows:
        if row["task"] != "rhythm":
            continue
        if row["excluded_reason"]:
            continue
        record = {key: row[key] for key in (
            "source", "split", "identity_hash", "group_hash", "targets", "mask", "classes"
        )}
        record.update({"scored": False, "window_count": 0, "error_type": None})
        rhythm_lookup[row["identity_hash"]] = len(rhythm_records)
        rhythm_records.append(record)

    rhythm_features, rhythm_logits, window_record_ids = {"P6": [], "P8": []}, {"P6": [], "P8": []}, []
    pending_samples, pending_links = [], []
    errors: Counter[str] = Counter()

    def flush_rhythm():
        if not pending_samples:
            return
        extracted = _rhythm_batch(rhythm_scorer, pending_samples)
        for profile in ("P6", "P8"):
            features, logits = extracted[profile]
            rhythm_features[profile].extend(features)
            rhythm_logits[profile].extend(logits)
        window_record_ids.extend(link[0] for link in pending_links)
        for record_index, _ in pending_links:
            rhythm_records[record_index]["scored"] = True
            rhythm_records[record_index]["window_count"] += 1
        pending_samples.clear()
        pending_links.clear()

    raw_root = data_root / "00_FUENTES_FISICAS_RAW"
    for row in rows:
        if row["task"] != "rhythm" or row["excluded_reason"]:
            continue
        record_index = rhythm_lookup[row["identity_hash"]]
        source_root = raw_root / row["source"]
        try:
            signal_path = _signal_path(source_root, row["relative_record"])
            if _sha256(signal_path) != row["signal_sha256"]:
                raise ValueError("waveform hash differs from preflight inventory")
            samples = prepare_rhythm_record(signal_path.with_suffix(""), morphology)
            if not samples:
                raise ValueError("preprocessor returned no windows")
        except (OSError, ValueError, RuntimeError, ImportError) as exc:
            errors[f"rhythm:{row['source']}:{type(exc).__name__}"] += 1
            rhythm_records[record_index]["error_type"] = type(exc).__name__
            continue
        for window_index, sample in enumerate(samples):
            pending_samples.append(sample)
            pending_links.append((record_index, window_index))
            if len(pending_samples) >= RHYTHM_BATCH_SIZE:
                flush_rhythm()
    flush_rhythm()

    pathology_records, pathology_features, pathology_scores = [], [], []
    pending_p4_samples, pending_p4_records = [], []
    row_lookup = [row for row in rows if row["task"] == "pathology" and not row["excluded_reason"]]

    def flush_pathology():
        if not pending_p4_samples:
            return
        features, scores = _pathology_batch(pathology_scorer, pending_p4_samples)
        pathology_features.extend(features)
        pathology_scores.extend(scores)
        for record_index in pending_p4_records:
            pathology_records[record_index]["scored"] = True
        pending_p4_samples.clear()
        pending_p4_records.clear()

    for row in row_lookup:
        record_index = len(pathology_records)
        record = {key: row[key] for key in (
            "source", "split", "identity_hash", "group_hash", "targets", "mask", "classes", "fold"
        )}
        record.update({"scored": False, "error_type": None})
        pathology_records.append(record)
        source_root = raw_root / "ptb-xl"
        try:
            signal_path = _signal_path(source_root, row["relative_record"])
            if _sha256(signal_path) != row["signal_sha256"]:
                raise ValueError("waveform hash differs from preflight inventory")
            sample = prepare_p4_record(signal_path.with_suffix(""), morphology)
        except (OSError, ValueError, RuntimeError, ImportError) as exc:
            errors[f"pathology:{type(exc).__name__}"] += 1
            pathology_records[record_index]["error_type"] = type(exc).__name__
            continue
        pending_p4_samples.append(sample)
        pending_p4_records.append(record_index)
        if len(pending_p4_samples) >= PATHOLOGY_BATCH_SIZE:
            flush_pathology()
    flush_pathology()

    rhythm_record_index = np.asarray(window_record_ids, dtype=np.int32)
    p4_record_index = np.asarray([i for i, row in enumerate(pathology_records) if row["scored"]], dtype=np.int32)
    rhythm_arrays = {
        "p6_features": np.asarray(rhythm_features["P6"], dtype=np.float32),
        "p8_features": np.asarray(rhythm_features["P8"], dtype=np.float32),
        "p6_baseline_logits": np.asarray(rhythm_logits["P6"], dtype=np.float32),
        "p8_baseline_logits": np.asarray(rhythm_logits["P8"], dtype=np.float32),
        "rhythm_record_index": rhythm_record_index,
        "p4_features": np.asarray(pathology_features, dtype=np.float32),
        "p4_baseline_scores": np.asarray(pathology_scores, dtype=np.float32),
        "p4_record_index": p4_record_index,
    }
    cache_path = output_dir / "private_frozen_features.npz"
    _atomic_npz(cache_path, **rhythm_arrays)
    metadata = {
        "schema": "TITAN_PRIVATE_SPECIALIST_FEATURE_CACHE_V1",
        "study_id": config["study_id"],
        "git_commit": _git_revision(repo),
        "config_sha256": _sha256(CONFIG),
        "preflight_receipt_sha256": _sha256(preflight_dir / "preflight_receipt.json"),
        "private_inventory_sha256": _sha256(inventory_path),
        "feature_cache_sha256": _sha256(cache_path),
        "release_manifest_sha256": _sha256(repo / "release-manifest.json"),
        "global_contract_sha256": _sha256(repo / "outputs/models/heads/global_head_contracts.json"),
        "baseline_asset_hashes": {**rhythm_hashes, **pathology_hashes},
        "baseline_thresholds": frozen_thresholds,
        "baseline_threshold_source_hashes": {
            "p6_calibration_lineage": _sha256(
                repo / "outputs/results/revision_20261029/p6_calibration_lineage_summary.json"
            ),
            "p8_external_development_metrics": _sha256(
                repo / "outputs/results/external_dev/rhythm_primary8_metrics.json"
            ),
            "p4_thresholds_embedded_in_asset": pathology_hashes[P4_SPECIALIST],
        },
        "preflight_aggregates": preflight["aggregates"],
        "morphology_candidate_sha256_lf": EXPECTED_MORPHOLOGY_SHA,
        "event_trainer_sha256": TRAINER_SHA,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": version("scipy"),
        "wfdb_version": version("wfdb"),
        "cuda_version": torch.version.cuda,
        "device": device,
        "device_name": torch.cuda.get_device_name(0) if device == "cuda" else platform.processor(),
        "window_aggregation": config["rhythm"]["window_aggregation"],
        "rhythm_records": rhythm_records,
        "pathology_records": pathology_records,
        "preprocessing_errors_by_source_and_type": dict(sorted(errors.items())),
        "performance_metrics_computed": False,
        "record_level_ids_or_scores_public": False,
    }
    _atomic_json(output_dir / "private_feature_metadata.json", metadata)
    print(json.dumps({
        "schema": "TITAN_SPECIALIST_FEATURE_EXTRACTION_RECEIPT_V1",
        "study_id": config["study_id"],
        "feature_cache_sha256": metadata["feature_cache_sha256"],
        "baseline_asset_hashes": metadata["baseline_asset_hashes"],
        "rhythm_records_scored": sum(row["scored"] for row in rhythm_records),
        "rhythm_windows": len(rhythm_record_index),
        "pathology_records_scored": len(p4_record_index),
        "errors_by_source_and_type": metadata["preprocessing_errors_by_source_and_type"],
        "performance_metrics_computed": False,
    }, sort_keys=True))
    return metadata


def _baseline_thresholds(repo: Path, pathology_scorer: FrozenPathology) -> dict[str, dict[str, float]]:
    p6_path = repo / "outputs/results/revision_20261029/p6_calibration_lineage_summary.json"
    p8_path = repo / "outputs/results/external_dev/rhythm_primary8_metrics.json"
    p6 = json.loads(p6_path.read_text(encoding="utf-8"))
    p8 = json.loads(p8_path.read_text(encoding="utf-8"))
    if (p6.get("aggregation") != "mean_logits" or p6.get("biases") != [0] * 6
            or tuple(p6.get("classes", ())) != ("AFIB", "SB", "STACH", "RBBB", "1AVB", "PVC")
            or tuple(p8.get("classes", ())) != (
                "AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"
            )):
        raise ValueError("baseline P6 score policy differs from the frozen configuration")
    result = {
        "P6": dict(zip(p6["classes"], map(float, p6["thresholds"]), strict=True)),
        "P8": dict(zip(p8["classes"], map(float, p8["thresholds"]), strict=True)),
        "P4": pathology_scorer.thresholds,
    }
    if any(not np.isfinite(value) or not 0 <= value <= 1
           for profile in result.values() for value in profile.values()):
        raise ValueError("baseline thresholds are non-finite or outside [0, 1]")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--preflight-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--asset-root", type=Path,
                        help="verified release asset cache; defaults to the repository root")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    args = parser.parse_args()
    run(args.data_root, args.preflight_dir, args.output_dir, args.repo, args.device, args.asset_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
