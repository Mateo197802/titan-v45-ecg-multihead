"""Run the frozen, aggregate-only SPH PAC-head comparison in authorized CEDIA storage."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
import tarfile
import time
from collections import defaultdict
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
import scipy
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.benchmarkmax.pac import (  # noqa: E402
    PAC_AGGREGATE_SCHEMA,
    _average_precision,
    assign_patient_split,
    binary_metrics,
    encode_v3f_token_sequences,
    fit_l2_logistic,
    fit_pac_mlp,
    fit_standardizer,
    patient_cluster_bootstrap,
    select_f1_threshold,
    validate_pac_aggregate,
)
from titan_v45.data.sph import (  # noqa: E402
    FS_HZ,
    LEADS,
    RECORD_ID,
    read_sph_dictionary,
    read_sph_metadata,
    read_sph_signal,
)
from titan_v45.data.sph_waveform import prepare_sph_waveform  # noqa: E402
from titan_v45.models.factory import build_titan_v45_backbone  # noqa: E402

PAC_CODE = 30
PAC_DESCRIPTION = "Atrial premature complex(es)"
NONCONDUCTED_PAC_CODE = 31
NONCONDUCTED_PAC_DESCRIPTION = "Atrial premature complexes, nonconducted"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_outside(path: Path, forbidden_roots: list[Path], name: str) -> None:
    resolved = path.resolve()
    for root in forbidden_roots:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise ValueError(f"{name} must remain outside all repository checkouts")


def read_label_blind_signal_index(metadata_path: Path) -> dict[str, int]:
    """Read only ECG identity and sample count; never inspect label columns here."""
    output: dict[str, int] = {}
    with metadata_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"ECG_ID", "N"}.issubset(reader.fieldnames or ()):
            raise ValueError("SPH metadata lacks the label-blind signal-index columns")
        for row in reader:
            record_id = row["ECG_ID"].strip()
            samples = int(row["N"])
            if not RECORD_ID.fullmatch(record_id) or samples < 1 or record_id in output:
                raise ValueError("invalid or duplicate ECG ID/sample count in signal index")
            output[record_id] = samples
    if not output:
        raise ValueError("SPH signal index is empty")
    return output


def load_frozen_p8_pac_scores(
    ledger_path: Path,
    receipt_path: Path,
    *,
    expected_ledger_sha256: str,
    expected_receipt_sha256: str,
    expected_job_id: str,
    expected_source_sha256: dict[str, str],
    expected_model_sha256: str,
    expected_records: int,
) -> dict[str, float]:
    """Load only the PAC score from a hash-bound, label-blind V4.5 SPH ledger."""
    if sha256_file(ledger_path) != expected_ledger_sha256:
        raise ValueError("frozen V4.5 P8 score ledger hash differs from the protocol")
    if sha256_file(receipt_path) != expected_receipt_sha256:
        raise ValueError("frozen V4.5 P8 scoring receipt hash differs from the protocol")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("schema") != "TITAN_V45_SPH_SCORING_RECEIPT_V1"
            or receipt.get("stage") != "full_population"
            or str(receipt.get("job_id")) != expected_job_id
            or receipt.get("ledger_sha256") != expected_ledger_sha256
            or receipt.get("source_sha256") != expected_source_sha256
            or receipt.get("model_sha256", {}).get(
                "specialists-v3q-primary8-best-candidate.pt"
            ) != expected_model_sha256
            or receipt.get("labels_used_for_inference_or_routing") is not False):
        raise ValueError("frozen V4.5 P8 receipt does not match the blinded baseline contract")
    flow = receipt.get("flow", {})
    if (flow.get("metadata_records") != expected_records
            or flow.get("archive_records") != expected_records
            or flow.get("scored_records") != expected_records
            or flow.get("status_counts") != {"scored": expected_records}):
        raise ValueError("frozen V4.5 P8 receipt does not cover the complete source population")

    scores: dict[str, float] = {}
    with ledger_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise ValueError("frozen V4.5 P8 score ledger contains an empty row")
            try:
                row = json.loads(line)
                record_id = row["record_id"]
                score = row["profiles"]["P8"]["scores"]["PAC"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(f"invalid P8 PAC ledger row at line {line_number}") from exc
            if (not isinstance(record_id, str) or not RECORD_ID.fullmatch(record_id)
                    or row.get("status") != "scored"):
                raise ValueError(f"invalid P8 PAC ledger identity/status at line {line_number}")
            if (isinstance(score, bool) or not isinstance(score, (int, float))
                    or not np.isfinite(score) or not 0 <= score <= 1):
                raise ValueError(f"invalid P8 PAC probability at line {line_number}")
            if record_id in scores:
                raise ValueError("frozen V4.5 P8 score ledger has duplicate ECG identities")
            scores[record_id] = float(score)
    if len(scores) != expected_records:
        raise ValueError("frozen V4.5 P8 score ledger does not reconcile to its full denominator")
    return scores


def load_frozen_backbone(weights_path: Path, device: torch.device) -> torch.nn.Module:
    checkpoint = torch.load(weights_path, map_location="cpu", weights_only=True)
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("state_dict"), dict):
        raise ValueError("V3F checkpoint does not contain a state_dict")
    model = build_titan_v45_backbone(morphology_dim=10)
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.requires_grad_(False)
    model.eval()
    return model.to(device)


def embed_record_batch(
    model: torch.nn.Module,
    batch: list[tuple[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]]],
    device: torch.device,
    *,
    windows_per_batch: int,
) -> dict[str, np.ndarray]:
    all_windows = []
    all_masks = []
    sections: list[tuple[str, int, int]] = []
    offset = 0
    for record_id, windows in batch:
        begin = offset
        for signal, mask, _ in windows:
            all_windows.append(signal)
            all_masks.append(mask)
            offset += 1
        sections.append((record_id, begin, offset))

    accumulators: dict[str, dict[str, object]] = {}
    with torch.inference_mode():
        for start in range(0, len(all_windows), windows_per_batch):
            stop = min(start + windows_per_batch, len(all_windows))
            x = torch.as_tensor(np.stack(all_windows[start:stop]), dtype=torch.float32, device=device)
            mask = torch.as_tensor(np.stack(all_masks[start:stop]), dtype=torch.bool, device=device)
            tokens, context = encode_v3f_token_sequences(model, x, mask)
            for record_id, record_start, record_stop in sections:
                low, high = max(record_start, start), min(record_stop, stop)
                if low >= high:
                    continue
                local = slice(low - start, high - start)
                selected = tokens[local]
                selected_context = context[local]
                partial_sum = selected.sum(dim=(0, 1))
                partial_max = selected.amax(dim=(0, 1))
                token_count = selected.shape[0] * selected.shape[1]
                current = accumulators.get(record_id)
                if current is None:
                    accumulators[record_id] = {
                        "sum": partial_sum,
                        "max": partial_max,
                        "count": token_count,
                        "context": selected_context[0],
                    }
                else:
                    current["sum"] = current["sum"] + partial_sum
                    current["max"] = torch.maximum(current["max"], partial_max)
                    current["count"] = int(current["count"]) + token_count
    pooled: dict[str, np.ndarray] = {}
    with torch.inference_mode():
        for record_id, current in accumulators.items():
            mean_pool = current["sum"] / int(current["count"])
            max_pool = current["max"]
            context = current["context"]
            mean_embedding = model.final_norm(mean_pool + context)
            max_embedding = model.final_norm(max_pool + context)
            values = torch.cat((mean_embedding, max_embedding)).cpu().numpy()
            pooled[record_id] = values.astype(np.float32, copy=False)
    if len(pooled) != len(batch):
        raise AssertionError("inference did not produce one embedding per eligible record")
    return pooled


def extract_embeddings(
    metadata_path: Path,
    dictionary_path: Path,
    waveform_path: Path,
    backbone_path: Path,
    *,
    device: torch.device,
    record_batch_size: int,
    windows_per_batch: int,
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    signal_index = read_label_blind_signal_index(metadata_path)
    primary, _ = read_sph_dictionary(dictionary_path.read_text(encoding="utf-8-sig"))
    if primary.get(PAC_CODE) != PAC_DESCRIPTION:
        raise ValueError("SPH dictionary PAC code 30 differs from the frozen endpoint")
    if primary.get(NONCONDUCTED_PAC_CODE) != NONCONDUCTED_PAC_DESCRIPTION:
        raise ValueError("SPH dictionary code 31 differs from its separate frozen meaning")

    model = load_frozen_backbone(backbone_path, device)
    seen: set[str] = set()
    fingerprints: dict[str, list[str]] = defaultdict(list)
    embeddings: dict[str, np.ndarray] = {}
    pending: list[tuple[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]]] = []
    counts: dict[str, int] = defaultdict(int)
    amplitude_peaks: list[float] = []

    def flush() -> None:
        nonlocal pending
        if pending:
            embeddings.update(
                embed_record_batch(
                    model, pending, device, windows_per_batch=windows_per_batch
                )
            )
            pending = []

    with tarfile.open(waveform_path, mode="r|*") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or "\\" in member.name
                    or len(path.parts) > 2):
                raise ValueError("unsafe path in SPH waveform archive")
            if member.isdir():
                continue
            if (not member.isfile() or path.suffix != ".h5"
                    or not RECORD_ID.fullmatch(path.stem)):
                raise ValueError("unexpected member type in SPH waveform archive")
            record_id = path.stem
            if record_id not in signal_index or record_id in seen:
                raise ValueError("unknown or duplicate ECG ID in waveform archive")
            seen.add(record_id)
            if not 0 < member.size <= 2 * 1024 * 1024:
                counts["invalid_hdf5_member_size"] += 1
                continue
            samples = signal_index[record_id]
            if not 10 * FS_HZ <= samples <= 60 * FS_HZ:
                counts["duration_outside_10_to_60_seconds"] += 1
                continue
            raw = archive.extractfile(member)
            if raw is None:
                counts["unreadable_archive_member"] += 1
                continue
            try:
                signal, _ = read_sph_signal(raw.read(), samples)
            except (ValueError, OSError):
                counts["invalid_hdf5_shape_dtype_or_signal"] += 1
                continue
            if not np.any(np.ptp(signal.astype(np.float64), axis=1) > 0):
                counts["all_leads_flat"] += 1
                continue

            canonical = np.asarray(signal, dtype="<f8")
            fingerprint = hashlib.sha256(canonical.tobytes()).hexdigest()
            fingerprints[fingerprint].append(record_id)
            amplitude_peaks.append(float(np.max(np.abs(canonical))))
            try:
                windows = prepare_sph_waveform(
                    signal,
                    lambda _values, fs: np.zeros(10, dtype=np.float32),
                    branch="rhythm",
                )
            except (ValueError, OSError, FloatingPointError):
                counts["preprocessing_failure"] += 1
                continue
            pending.append((record_id, windows))
            counts["technically_valid_signals"] += 1
            counts["windows_processed"] += len(windows)
            if len(pending) >= record_batch_size:
                flush()
                print(f"Embedded {len(embeddings)} ECGs", flush=True)
    flush()

    if seen != signal_index.keys():
        raise ValueError(
            f"waveform archive population differs from metadata index: "
            f"missing={len(signal_index.keys() - seen)}"
        )
    duplicate_groups = [group for group in fingerprints.values() if len(group) > 1]
    duplicate_records = {record_id for group in duplicate_groups for record_id in group}
    for record_id in duplicate_records:
        embeddings.pop(record_id, None)
    counts["exact_duplicate_signal_groups_excluded"] = len(duplicate_groups)
    counts["exact_duplicate_signal_excess_records"] = sum(
        len(group) - 1 for group in duplicate_groups
    )
    counts["exact_duplicate_records_excluded"] = len(duplicate_records)
    counts["eligible_unique_records"] = len(embeddings)
    counts["source_records"] = len(signal_index)
    counts["archive_members_seen"] = len(seen)
    counts["waveform_units_documented"] = 0
    amplitude_summary = {
        "unit": "source amplitude units are not documented as mV; values are unitless",
        "absolute_peak_quantiles_across_records": (
            np.quantile(amplitude_peaks, [0.5, 0.95, 0.99]).tolist()
            if amplitude_peaks else []
        ),
        "amplitude_exclusion_threshold_applied": False,
        "technical_amplitude_rule": "finite values and at least one non-flat lead",
    }
    return embeddings, {"counts": dict(sorted(counts.items())), "amplitude": amplitude_summary}


def load_labels(metadata_path: Path, dictionary_path: Path) -> dict[str, tuple[str, int, int]]:
    primary, modifier = read_sph_dictionary(dictionary_path.read_text(encoding="utf-8-sig"))
    if primary.get(PAC_CODE) != PAC_DESCRIPTION:
        raise ValueError("PAC code 30 description changed after the frozen dictionary check")
    rows = read_sph_metadata(metadata_path.read_text(encoding="utf-8-sig"), primary, modifier)
    return {
        record_id: (
            entry.patient,
            int(PAC_CODE in entry.primary_codes),
            int(NONCONDUCTED_PAC_CODE in entry.primary_codes),
        )
        for record_id, entry in rows.items()
    }


def validate_source_statement_counts(
    labels: dict[str, tuple[str, int, int]],
    source_config: dict[str, object],
) -> dict[str, int]:
    expected = source_config.get("source_statement_counts_before_signal_exclusions")
    if (not isinstance(expected, dict)
            or set(expected) != {
                "code_30_records", "code_31_records", "counts_verified_against_source_inventory",
            }
            or expected.get("counts_verified_against_source_inventory") is not True
            or any(type(expected[key]) is not int or expected[key] < 0
                   for key in ("code_30_records", "code_31_records"))):
        raise ValueError("frozen source statement supports are malformed")
    actual = {
        "code_30_records": sum(code30 for _, code30, _ in labels.values()),
        "code_31_records": sum(code31 for _, _, code31 in labels.values()),
    }
    if actual != {
        key: expected[key] for key in ("code_30_records", "code_31_records")
    }:
        raise ValueError("source PAC statement supports differ from the frozen inventory")
    return actual


def _support_view(
    selected: dict[str, tuple[str, int, int]], row_split: dict[str, str]
) -> dict[str, dict[str, int]]:
    support = {
        name: {"records": 0, "patients": 0, "positive_records": 0, "positive_patients": 0}
        for name in ("train", "development", "exploratory_holdout")
    }
    patients = {name: set() for name in support}
    positives = {name: set() for name in support}
    for record_id, (patient_id, label, _) in selected.items():
        split = row_split[record_id]
        support[split]["records"] += 1
        patients[split].add(patient_id)
        if label:
            support[split]["positive_records"] += 1
            positives[split].add(patient_id)
    for name in support:
        support[name]["patients"] = len(patients[name])
        support[name]["positive_patients"] = len(positives[name])
    return support


def _validate_partition_labels(support: dict[str, dict[str, int]]) -> None:
    for name, values in support.items():
        if values["records"] == 0 or values["positive_records"] == 0:
            raise ValueError(f"{name} lacks PAC statement-positive record support")
        if values["positive_records"] == values["records"]:
            raise ValueError(f"{name} lacks PAC statement-not-recorded support")


def run(args: argparse.Namespace) -> None:
    config_path = args.config.resolve()
    config_digest = sha256_file(config_path)
    if config_digest != args.expected_config_sha256:
        raise ValueError("PAC protocol config SHA-256 differs from the frozen expected value")

    source = args.source.resolve()
    metadata_path = source / "metadata.csv"
    dictionary_path = source / "code.csv"
    waveform_path = source / "records.tar.gz"
    inventory_path = ROOT / "outputs/results/external_sph/source_inventory_32617.json"
    backbone_path = args.backbone.resolve()
    p8_specialist_path = args.p8_specialist.resolve()
    p8_ledger_path = args.p8_ledger.resolve()
    p8_receipt_path = args.p8_receipt.resolve()
    output_path = args.output.resolve()
    forbidden_roots = [ROOT, *(path.resolve() for path in args.forbidden_root)]
    check_outside(output_path, forbidden_roots, "private result")
    check_outside(p8_ledger_path, forbidden_roots, "private V4.5 P8 score ledger")
    check_outside(p8_receipt_path, forbidden_roots, "private V4.5 P8 scoring receipt")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("schema") != PAC_AGGREGATE_SCHEMA:
        raise ValueError("unexpected frozen PAC protocol schema")
    expected_hashes = config["input_sha256"]
    input_paths = {
        "metadata": metadata_path, "dictionary": dictionary_path,
        "waveform_archive": waveform_path, "source_inventory": inventory_path,
        "backbone": backbone_path, "p8_specialist": p8_specialist_path,
        "v45_p8_score_ledger": p8_ledger_path,
        "v45_p8_scoring_receipt": p8_receipt_path,
    }
    actual_hashes = {name: sha256_file(path) for name, path in input_paths.items()}
    if actual_hashes != expected_hashes:
        raise ValueError("SPH or V3F input checksum differs from frozen protocol")
    source_inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    expected_inventory = config["source_inventory"]
    inventory_checks = {
        "schema": expected_inventory["schema"],
        "metadata_ecgs": expected_inventory["records"],
        "metadata_patients": expected_inventory["patients"],
        "valid_signal_ecgs": expected_inventory["valid_signal_records"],
        "technical_failures": expected_inventory["technical_failures"],
        "exact_duplicate_signal_groups": expected_inventory["exact_duplicate_signal_groups"],
        "exact_duplicate_signal_excess_records": expected_inventory[
            "exact_duplicate_signal_excess_records"
        ],
        "scope": expected_inventory["scope"],
    }
    if any(source_inventory.get(key) != value for key, value in inventory_checks.items()):
        raise ValueError("frozen source inventory contradicts its declared contents")
    if output_path.exists():
        raise FileExistsError("private output already exists; use a fresh run directory")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if stat.S_IMODE(output_path.parent.stat().st_mode) & 0o077:
        raise ValueError("private run directory must not grant group or other permissions")

    expected_commit = args.expected_commit
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if current_commit != expected_commit:
        raise ValueError("checkout commit differs from the frozen run declaration")
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if dirty:
        raise ValueError("benchmark checkout must be clean before this run")

    runtime = {
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "torch": torch.__version__, "cuda": torch.version.cuda,
        "h5py": h5py.__version__,
    }
    runtime_config = config["runtime"]
    for key in ("python", "numpy", "scipy", "torch", "h5py"):
        if runtime[key] != runtime_config[key]:
            raise ValueError(f"runtime {key} differs from frozen protocol")
    if runtime["cuda"] != runtime_config["cuda"]:
        raise ValueError("CUDA runtime differs from the frozen protocol")
    if (not torch.cuda.is_available()
            or torch.cuda.get_device_name(0) != runtime_config["device"]):
        raise ValueError("the frozen SPH head comparison requires a CUDA device")

    torch.set_num_threads(config["runtime"]["torch_threads"])
    torch.manual_seed(config["training"]["seed"])
    torch.cuda.manual_seed_all(config["training"]["seed"])
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if hasattr(torch.backends.cuda, "enable_flash_sdp"):
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
    device = torch.device("cuda:0")

    started = time.monotonic()
    embeddings, extraction = extract_embeddings(
        metadata_path, dictionary_path, waveform_path, backbone_path,
        device=device,
        record_batch_size=config["inference"]["record_batch_size"],
        windows_per_batch=config["inference"]["windows_per_batch"],
    )
    expected_source = config["source"]
    if extraction["counts"]["source_records"] != expected_source["records"]:
        raise ValueError("SPH source record count differs from the frozen protocol")
    if (extraction["counts"]["archive_members_seen"] != expected_inventory["records"]
            or extraction["counts"]["technically_valid_signals"]
            != expected_inventory["valid_signal_records"]):
        raise ValueError("runtime signal population differs from the audited source inventory")
    if (extraction["counts"]["exact_duplicate_signal_groups_excluded"]
            != expected_inventory["exact_duplicate_signal_groups"]
            or extraction["counts"]["exact_duplicate_signal_excess_records"]
            != expected_inventory["exact_duplicate_signal_excess_records"]):
        raise ValueError("runtime exact-duplicate counts differ from the frozen source audit")

    # Labels and patients are deliberately read only after waveform inference has finished.
    labels = load_labels(metadata_path, dictionary_path)
    if len(labels) != expected_source["records"]:
        raise ValueError("SPH label population differs from the frozen protocol")
    actual_statement_counts = validate_source_statement_counts(labels, expected_source)
    source_patients = len({patient for patient, _, _ in labels.values()})
    if source_patients != expected_source["patients"]:
        raise ValueError("SPH patient count differs from the frozen protocol")
    if not set(embeddings).issubset(labels):
        raise ValueError("an eligible waveform has no source label row")
    p8_config = config["p8_baseline"]
    p8_scores = load_frozen_p8_pac_scores(
        p8_ledger_path,
        p8_receipt_path,
        expected_ledger_sha256=p8_config["ledger_sha256"],
        expected_receipt_sha256=p8_config["receipt_sha256"],
        expected_job_id=p8_config["job_id"],
        expected_source_sha256={
            "metadata.csv": actual_hashes["metadata"],
            "code.csv": actual_hashes["dictionary"],
            "records.tar.gz": actual_hashes["waveform_archive"],
        },
        expected_model_sha256=actual_hashes["p8_specialist"],
        expected_records=p8_config["expected_records"],
    )
    if set(p8_scores) != set(labels):
        raise ValueError("frozen V4.5 P8 scores do not match the SPH metadata population")

    selected = {record_id: labels[record_id] for record_id in embeddings}
    row_split = {}
    for record_id, (patient, _, _) in selected.items():
        assigned = assign_patient_split(patient)
        row_split[record_id] = (
            "exploratory_holdout" if assigned == "calibration" else assigned
        )
    split_support = _support_view(selected, row_split)
    _validate_partition_labels(split_support)
    ordered_ids = sorted(selected)
    matrix = np.stack([embeddings[record_id] for record_id in ordered_ids]).astype(np.float32)
    y = np.asarray([selected[record_id][1] for record_id in ordered_ids], dtype=np.int8)
    patient_ids = np.asarray([selected[record_id][0] for record_id in ordered_ids])
    splits = np.asarray([row_split[record_id] for record_id in ordered_ids])
    train_mask = splits == "train"
    dev_mask = splits == "development"
    holdout_mask = splits == "exploratory_holdout"
    if np.any(np.isin(patient_ids[train_mask], patient_ids[dev_mask])):
        raise AssertionError("train and development patients overlap")
    if np.any(np.isin(patient_ids[train_mask], patient_ids[holdout_mask])):
        raise AssertionError("train and exploratory holdout patients overlap")
    if np.any(np.isin(patient_ids[dev_mask], patient_ids[holdout_mask])):
        raise AssertionError("development and exploratory holdout patients overlap")

    scaler = fit_standardizer(matrix[train_mask])
    standardized = scaler.transform(matrix).astype(np.float32)
    p8_holdout_scores = np.asarray(
        [p8_scores[record_id] for record_id in ordered_ids], dtype=np.float64
    )[holdout_mask]
    p8_threshold = float(p8_config["threshold"])
    p8_metrics = binary_metrics(
        y[holdout_mask], p8_holdout_scores, threshold=p8_threshold,
        ece_bins=config["metrics"]["ece_bins"],
    )
    logistic = fit_l2_logistic(
        standardized[train_mask], y[train_mask],
        c_value=config["training"]["logistic_regression"]["c_value"],
    )
    if not logistic.converged:
        raise ValueError("frozen logistic-regression optimizer did not converge")
    logistic_dev_scores = logistic.predict_proba(standardized[dev_mask])
    logistic_threshold = select_f1_threshold(y[dev_mask], logistic_dev_scores)
    logistic_holdout_scores = logistic.predict_proba(standardized[holdout_mask])
    logistic_metrics = binary_metrics(
        y[holdout_mask], logistic_holdout_scores, threshold=logistic_threshold,
        ece_bins=config["metrics"]["ece_bins"],
    )

    mlp_results: dict[int, dict[str, object]] = {}
    mlp_fits = {}
    for seed in config["training"]["mlp"]["seeds"]:
        mlp_fit = fit_pac_mlp(
            standardized[train_mask], y[train_mask], standardized[dev_mask], y[dev_mask],
            seed=seed,
            max_epochs=config["training"]["mlp"]["max_epochs"],
            patience=config["training"]["mlp"]["patience"],
            batch_size=config["training"]["mlp"]["batch_size"],
            learning_rate=config["training"]["mlp"]["learning_rate"],
            weight_decay=config["training"]["mlp"]["weight_decay"],
            hidden_dim=config["training"]["mlp"]["hidden_dim"],
            dropout=config["training"]["mlp"]["dropout"],
            device=str(device),
        )
        mlp_fits[seed] = mlp_fit
        dev_scores = mlp_fit.predict_proba(standardized[dev_mask])
        threshold = select_f1_threshold(y[dev_mask], dev_scores)
        holdout_scores = mlp_fit.predict_proba(standardized[holdout_mask])
        mlp_results[seed] = {
            "threshold": threshold,
            "development_average_precision": float(_average_precision(y[dev_mask], dev_scores)),
            "exploratory_holdout_metrics": binary_metrics(
                y[holdout_mask], holdout_scores, threshold=threshold,
                ece_bins=config["metrics"]["ece_bins"],
            ),
            "holdout_scores": holdout_scores,
        }

    model_scores = {
        "frozen_v45_p8_pac": (p8_holdout_scores, p8_threshold),
        "logistic_regression": (logistic_holdout_scores, logistic_threshold),
        **{
            f"mlp_seed_{seed}": (result["holdout_scores"], result["threshold"])
            for seed, result in mlp_results.items()
        },
    }
    bootstrap_pairs = [("frozen_v45_p8_pac", "logistic_regression")]
    for seed in config["training"]["mlp"]["seeds"]:
        name = f"mlp_seed_{seed}"
        bootstrap_pairs.extend((("frozen_v45_p8_pac", name), ("logistic_regression", name)))
    bootstrap_comparisons = {}
    for reference, candidate in bootstrap_pairs:
        key = f"{candidate}_minus_{reference}"
        pair = patient_cluster_bootstrap(
            y[holdout_mask], model_scores[reference][0], model_scores[candidate][0],
            patient_ids[holdout_mask], model_scores[reference][1], model_scores[candidate][1],
            replicates=config["metrics"]["bootstrap_replicates"],
            seed=config["metrics"]["bootstrap_seed"],
        )
        bootstrap_comparisons[key] = {
            "reference_model": reference,
            "candidate_model": candidate,
            "metrics": pair["metrics"],
            "valid_replicates": pair["valid_replicates"],
            "invalid_replicates": pair["invalid_replicates"],
        }
    bootstrap = {
        "unit": "patient_id cluster; repeated ECGs sampled together",
        "method": "paired unstratified percentile bootstrap",
        "replicates": config["metrics"]["bootstrap_replicates"],
        "seed": config["metrics"]["bootstrap_seed"],
        "comparisons": bootstrap_comparisons,
    }

    artifact_path = output_path.with_name("pac_heads_private.pt")
    if artifact_path.exists():
        raise FileExistsError("private model artifact already exists; use a fresh run directory")
    artifact = {
        "schema": "TITAN_V46_SPH_PAC_HEADS_PRIVATE_V1",
        "protocol_sha256": config_digest,
        "training_feature_mean": torch.from_numpy(scaler.mean.astype(np.float32)),
        "training_feature_scale": torch.from_numpy(scaler.scale.astype(np.float32)),
        "logistic_coefficients": torch.from_numpy(logistic.coefficients.astype(np.float32)),
        "logistic_intercept": logistic.intercept,
        "mlp_state_dicts": {
            str(seed): {
                key: value.detach().cpu()
                for key, value in mlp_fit.model.state_dict().items()
            }
            for seed, mlp_fit in mlp_fits.items()
        },
    }
    torch.save(artifact, artifact_path)
    os.chmod(artifact_path, 0o600)

    report: dict[str, object] = {
        "schema": PAC_AGGREGATE_SCHEMA,
        "scope": (
            "Exploratory development/adaptation on previously observed SPH; not independent, "
            "external, confirmatory, clinical, or prospective validation."
        ),
        "protocol": {
            "config_sha256": config_digest,
            "protocol_sha256": sha256_file(ROOT / "docs/benchmarkmax/SPH_PAC_HEAD_COMPARISON_PROTOCOL.md"),
            "runner_sha256": sha256_file(Path(__file__).resolve()),
            "verifier_sha256": sha256_file(
                ROOT / "scripts/benchmarkmax/verify_sph_pac_head_aggregate.py"
            ),
            "slurm_wrapper_sha256": sha256_file(
                ROOT / "scripts/cedia/run_sph_pac_head_comparison.sbatch"
            ),
            "git_commit": current_commit,
        },
        "inputs": actual_hashes,
        "runtime_archives_sha256": config["runtime_archives_sha256"],
        "source": {
            "name": "SPH ECG dataset V1",
            "reference": "AHA code 30 present on an ECG; absence is statement-not-recorded, not disease-negative",
            "nonconducted_pac_code_31_kept_separate": True,
            "source_statement_counts_before_signal_exclusions": actual_statement_counts,
            "native_sampling_hz": FS_HZ,
            "lead_order": list(LEADS),
        },
        "cohort": {
            "source_records": expected_source["records"],
            "source_patients": source_patients,
            "eligible_records": len(selected),
            "excluded_records": expected_source["records"] - len(selected),
            "exclusions": extraction["counts"],
            "split_support": split_support,
            "patient_overlap_across_splits": 0,
            "labels_used_for_split_assignment": False,
            "code_31_records_with_code_30_not_recorded": sum(
                code31 and not code30 for _, code30, code31 in selected.values()
            ),
            "code_30_and_code_31_co_recorded": sum(
                code30 and code31 for _, code30, code31 in selected.values()
            ),
            "exact_duplicate_groups_removed_before_label_join": extraction["counts"]["exact_duplicate_signal_groups_excluded"],
            "baseline_p8_scores_available_source_records": len(p8_scores),
            "baseline_p8_common_eligible_records": sum(record_id in p8_scores for record_id in selected),
        },
        "signal_quality": extraction["amplitude"],
        "representation": {
            "backbone": "frozen public V3F backbone; no backbone updates",
            "embedding": "temporal token mean and max over all 10-second windows, concatenated to 1280 dimensions",
            "window_schedule": "10 seconds; 5-second stride; reconstructed rhythm preprocessing; all windows of a record pooled",
            "preprocessing": "500 Hz native; third-order 0.5-45 Hz causal Butterworth; polyphase resample to 125 Hz; per-lead z-score; 10-second window with 2-second context padding",
            "historical_loader_equivalence_claim": False,
            "unit_conversion_to_millivolts": False,
        },
        "p8_baseline": {
            "job_id": p8_config["job_id"],
            "ledger_sha256": p8_config["ledger_sha256"],
            "receipt_sha256": p8_config["receipt_sha256"],
            "checkpoint_sha256": p8_config["checkpoint_sha256"],
            "threshold": p8_threshold,
        },
        "models": {
            "frozen_v45_p8_pac": {
                "threshold": p8_threshold,
                "development_average_precision": float(
                    _average_precision(y[dev_mask], np.asarray(
                        [p8_scores[record_id] for record_id in ordered_ids], dtype=np.float64
                    )[dev_mask])
                ),
                "exploratory_holdout_metrics": p8_metrics,
            },
            "logistic_regression": {
                "c_value": config["training"]["logistic_regression"]["c_value"],
                "optimizer": "SciPy L-BFGS-B; unweighted mean binary log loss; L2 on coefficients only",
                "threshold": logistic_threshold,
                "development_average_precision": float(
                    _average_precision(y[dev_mask], logistic_dev_scores)
                ),
                "exploratory_holdout_metrics": logistic_metrics,
            },
            **{
                f"mlp_seed_{seed}": {
                    "seed": seed,
                    "hidden_dim": config["training"]["mlp"]["hidden_dim"],
                    "dropout": config["training"]["mlp"]["dropout"],
                    "optimizer": "AdamW; unweighted BCEWithLogitsLoss; early stop on development average precision",
                    "epochs_trained": mlp_fits[seed].epochs_trained,
                    "best_development_average_precision": mlp_fits[seed].best_dev_average_precision,
                    "threshold": mlp_results[seed]["threshold"],
                    "development_average_precision": mlp_results[seed]["development_average_precision"],
                    "exploratory_holdout_metrics": mlp_results[seed]["exploratory_holdout_metrics"],
                }
                for seed in config["training"]["mlp"]["seeds"]
            },
        },
        "paired_patient_cluster_bootstrap": bootstrap,
        "private_model_artifact": {
            "filename": artifact_path.name,
            "sha256": sha256_file(artifact_path),
        },
        "runtime": runtime,
        "execution": {
            "slurm_job_id": os.environ.get("SLURM_JOB_ID", "not_slurm"),
            "device_name": torch.cuda.get_device_name(device),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        },
        "privacy": {
            "individual_identifiers_exported": False,
            "record_level_scores_exported": False,
            "raw_signals_exported": False,
            "embeddings_exported": False,
        },
    }
    validate_pac_aggregate(report)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    os.chmod(output_path, 0o600)
    print(json.dumps({"report": str(output_path), "sha256": sha256_file(output_path)}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--backbone", type=Path, required=True)
    parser.add_argument("--p8-specialist", type=Path, required=True)
    parser.add_argument("--p8-ledger", type=Path, required=True)
    parser.add_argument("--p8-receipt", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/benchmarkmax/sph_pac_head_comparison.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--forbidden-root", action="append", default=[], type=Path)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
