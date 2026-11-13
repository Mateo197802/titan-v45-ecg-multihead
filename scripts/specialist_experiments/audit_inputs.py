"""Create a private, row-level CEDIA inventory and a public-safe preflight receipt."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.training.specialist_heads import (  # noqa: E402
    P4_CLASSES,
    RHYTHM_CLASSES_P8,
    ptbxl_p4_targets,
    rhythm_targets,
    split_bucket,
    stable_fraction,
)

CONFIG = ROOT / "configs/specialist_heads/study_20261111_v2.json"
PTBXL_DATABASE_SHA256 = "7600de9c1b27d181d850b3c6038a35d7c3ddb6bb33b702e3a20252a6859d216b"
PTBXL_SCP_SHA256 = "ad05b0b1fcae83bb1230755ad9cfc7c96f303feddc08a4a9ad5bdc9ca63bac8f"
RHYTHM_SUPPORT = {
    "chapman_shaoxing": RHYTHM_CLASSES_P8,
    "cpsc2018": ("AFIB", "NSR", "RBBB", "PAC", "1AVB"),
    "georgia": ("AFIB", "SB", "STACH", "RBBB", "PAC", "1AVB", "PVC"),
}
RHYTHM_ROOTS = tuple(RHYTHM_SUPPORT)
GEORGIA_SOURCE_HOLDOUT_SUPPORT = frozenset(RHYTHM_SUPPORT["georgia"])
SOURCE_PRIORITY = {"chapman_shaoxing": 0, "cpsc2018": 1, "georgia": 2, "ptbxl": 3}
SOURCE_DIRECTORY_NAMES = {"ptbxl": "ptb-xl"}
SPLIT_PRIORITY = {"train": 0, "validation": 1, "calibration": 2, "internal_evaluation": 3,
                  "source_holdout": 4}
PUBLIC_RHYTHM_SOURCE_ALIASES = {
    "chapman_shaoxing": "chapman_shaoxing",
    "training/cpsc_2018": "cpsc2018",
    "training/cpsc_2018_extra": "cpsc2018",
    "training/georgia": "georgia",
}
IO_WORKERS = 4
PROGRESS_INTERVAL = 1000


class WaveformIntegrityError(Exception):
    """Raised when a waveform changed after its private inventory was sealed."""


def _parallel_map(stage: str, function, items: list[Any]) -> list[Any]:
    if not items:
        return []
    results: list[Any] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=min(IO_WORKERS, len(items))) as executor:
        futures = {executor.submit(function, item): index for index, item in enumerate(items)}
        for completed, future in enumerate(as_completed(futures), start=1):
            results[futures[future]] = future.result()
            if completed == 1 or completed % PROGRESS_INTERVAL == 0 or completed == len(items):
                print(f"[preflight] {stage}: {completed}/{len(items)}", flush=True)
    return results


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_relative(path: Path, root: Path) -> str:
    if path.is_symlink() or path.resolve().is_relative_to(root.resolve()) is False:
        raise ValueError("source path is a symlink or escapes its authorized root")
    return path.resolve().relative_to(root.resolve()).as_posix()


def _hash_identity(source: str, relative: str) -> str:
    return hashlib.sha256(f"{source}\0{relative}".encode()).hexdigest()


def _read_dx(header: Path) -> set[str]:
    values: set[str] = set()
    for line in header.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        match = re.match(r"^#\s*Dx\s*:\s*(.*)$", line.strip(), flags=re.IGNORECASE)
        if match:
            values.update(code.strip() for code in match.group(1).split(",") if code.strip())
    return values


def _header_summary(header: Path, wfdb_module) -> dict[str, float | int]:
    parsed = wfdb_module.rdheader(str(header.with_suffix("")))
    try:
        lead_count = int(parsed.n_sig)
        sample_rate = float(parsed.fs)
        sample_count = int(parsed.sig_len)
    except (TypeError, ValueError) as exc:
        raise ValueError("WFDB parser returned invalid sampling metadata") from exc
    if lead_count < 1 or sample_rate <= 0 or sample_count < 1:
        raise ValueError("WFDB header contains nonpositive sampling metadata")
    return {"lead_count": lead_count, "sample_rate_hz": sample_rate,
            "duration_seconds": sample_count / sample_rate}


def _read_scp_codes(value: str) -> dict[str, float]:
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, dict):
        raise ValueError("PTB-XL scp_codes is not a dictionary")
    result = {}
    for code, likelihood in parsed.items():
        if not isinstance(code, str):
            raise ValueError("PTB-XL SCP code is not text")
        number = float(likelihood)
        if not 0 <= number <= 100:
            raise ValueError("PTB-XL SCP likelihood is outside [0, 100]")
        result[code] = number
    return result


def _public_exposed_rhythm_records(
    repo: Path, config: dict[str, Any]
) -> tuple[dict[str, set[str]], dict[str, Any]]:
    policy = config["data_policy"]["prior_v45_public_rhythm_evaluation_records"]
    exposed: dict[str, set[str]] = defaultdict(set)
    manifest_keys: dict[str, dict[str, set[str]]] = {}
    manifest_rows: dict[str, int] = {}
    manifest_hashes: dict[str, str] = {}
    for item in policy["manifests"]:
        path = repo / item["path"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise ValueError("pinned prior V4.5 evaluation manifest is missing or has a hash mismatch")
        manifest_keys[item["path"]] = defaultdict(set)
        manifest_rows[item["path"]] = 0
        manifest_hashes[item["path"]] = item["sha256"]
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                manifest_rows[item["path"]] += 1
                source = PUBLIC_RHYTHM_SOURCE_ALIASES.get(row.get("source", "").casefold())
                if source is None:
                    continue
                for field in ("record_id", "record_base"):
                    value = row.get(field, "")
                    if value:
                        record_name = Path(value).stem.casefold()
                        exposed[source].add(record_name)
                        manifest_keys[item["path"]][source].add(record_name)
    p8_path = "data/manifests/external_dev/rhythm_primary8_records.csv"
    p6_path = "data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv"
    sources = sorted(set(exposed) | {
        source for records in manifest_keys.values() for source in records
    })
    receipt = {
        "manifests": [
            {
                "path": path,
                "sha256": manifest_hashes[path],
                "rows": manifest_rows[path],
                "matched_unique_records_by_source": {
                    source: len(records) for source, records in sorted(manifest_keys[path].items())
                },
            }
            for path in sorted(manifest_keys)
        ],
        "p6_p8_overlap_unique_records_by_source": {
            source: len(
                manifest_keys.get(p6_path, {}).get(source, set())
                & manifest_keys.get(p8_path, {}).get(source, set())
            )
            for source in sources
        },
        "union_unique_records_by_source": {
            source: len(
                manifest_keys.get(p6_path, {}).get(source, set())
                | manifest_keys.get(p8_path, {}).get(source, set())
            )
            for source in sources
        },
        "matching_policy": "source alias plus case-folded record basename; IDs are not emitted",
    }
    return dict(exposed), receipt


def _challenge_records(
    data_root: Path, config: dict[str, Any], repo: Path, *, wfdb_module
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = data_root / "00_FUENTES_FISICAS_RAW"
    exposed_records, prior_eval_receipt = _public_exposed_rhythm_records(repo, config)

    def discover(source: str) -> tuple[str, Path, list[Path]]:
        source_root = raw / source
        if not source_root.is_dir() or source_root.is_symlink():
            raise ValueError(f"required authorized source is missing or a symlink: {source}")
        return source, source_root, sorted(source_root.rglob("*.hea"))

    discovered = _parallel_map("rhythm source discovery", discover, list(RHYTHM_ROOTS))
    candidates = [(source, source_root, header) for source, source_root, headers in discovered
                  for header in headers]

    def build_row(item: tuple[str, Path, Path]) -> dict[str, Any] | None:
        source, source_root, header = item
        relative = _safe_relative(header, source_root)
        signal = header.with_suffix(".mat")
        if not signal.exists():
            signal = header.with_suffix(".dat")
        if signal.is_symlink():
            raise ValueError(f"signal file is a symlink within source: {source}")
        if not signal.is_file():
            return None
        if not signal.resolve().is_relative_to(source_root.resolve()):
            raise ValueError(f"signal file escapes authorized source root: {source}")
        dx = _read_dx(header)
        if not dx:
            return None
        classes = RHYTHM_CLASSES_P8
        supported = tuple(name for name in classes if name in RHYTHM_SUPPORT[source])
        targets, mask = rhythm_targets(dx, classes, supported_classes=supported)
        identity = _hash_identity(source, relative)
        record_name = Path(relative).stem.casefold()
        split = "train"
        reason = None
        if source == "chapman_shaoxing":
            split = split_bucket(
                relative.replace("\\", "/"), seed=int(config["rhythm"]["chapman_split"]["seed"]),
                namespace=config["study_id"], train_fraction=0.8, validation_fraction=0.1,
            )
        elif source == "georgia":
            split = "source_holdout"
        if record_name in exposed_records.get(source, set()):
            reason = "previous_public_v45_evaluation_record"
        try:
            signal_spec = _header_summary(header, wfdb_module)
        except (OSError, TypeError, ValueError) as exc:
            signal_spec = {}
            reason = reason or "invalid_wfdb_header"
            header_parse_error = type(exc).__name__
        else:
            header_parse_error = None
        row = {
            "task": "rhythm",
            "source": source,
            "relative_record": relative[:-4] if relative.lower().endswith(".hea") else relative,
            "identity_hash": identity,
            "group_hash": identity if source == "chapman_shaoxing" else None,
            "signal_sha256": _sha256(signal),
            "split": split,
            "excluded_reason": reason,
            "targets": targets.astype(int).tolist(),
            "mask": mask.astype(int).tolist(),
            "classes": list(classes),
            **signal_spec,
        }
        if header_parse_error is not None:
            row["header_parse_error_type"] = header_parse_error
        return row

    rows = [row for row in _parallel_map("rhythm records", build_row, candidates) if row is not None]
    rows.sort(key=lambda row: (SOURCE_PRIORITY[row["source"]], row["relative_record"].casefold()))
    return rows, prior_eval_receipt


def _ptbxl_records(
    data_root: Path, config: dict[str, Any], *, wfdb_module
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = data_root / "00_FUENTES_FISICAS_RAW" / "ptb-xl"
    if not root.is_dir() or root.is_symlink():
        raise ValueError("PTB-XL source root is missing or a symlink")
    metadata_path, statements_path = root / "ptbxl_database.csv", root / "scp_statements.csv"
    if any(path.is_symlink() or not path.resolve().is_relative_to(root.resolve())
           for path in (metadata_path, statements_path)):
        raise ValueError("PTB-XL metadata file is a symlink or escapes its source root")
    metadata_hash, statements_hash = _sha256(metadata_path), _sha256(statements_path)
    if metadata_hash != PTBXL_DATABASE_SHA256 or statements_hash != PTBXL_SCP_SHA256:
        raise ValueError("PTB-XL metadata or statement file hash differs from the audited v1.0.3 copy")

    prepared_rows: list[dict[str, Any]] = []
    patients_by_fold: dict[str, set[str]] = defaultdict(set)
    metadata_count = 0
    with metadata_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            metadata_count += 1
            fold = int(float(row["strat_fold"]))
            if fold == 10:
                continue
            if fold not in range(1, 10):
                raise ValueError("PTB-XL fold must lie in 1..10")
            patient_id = str(int(float(row["patient_id"])))
            patient_hash = hashlib.sha256(f"ptbxl_patient\0{patient_id}".encode()).hexdigest()
            patients_by_fold[patient_hash].add(str(fold))
            relative = Path(row["filename_lr"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe PTB-XL relative waveform path")
            base = root / relative
            header, signal = base.with_suffix(".hea"), base.with_suffix(".dat")
            if fold <= 7:
                split = "train"
            elif fold == 8:
                split = "validation"
            else:
                bucket = stable_fraction(
                    patient_hash, seed=int(config["pathology"]["split"]["seed"]),
                    namespace=f"{config['study_id']}:ptbxl-fold9",
                )
                split = "calibration" if bucket < 0.5 else "internal_evaluation"
            prepared_rows.append({
                "row": row,
                "fold": fold,
                "patient_hash": patient_hash,
                "relative": relative,
                "header": header,
                "signal": signal,
                "split": split,
            })

    def build_pathology_record(item: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
        row = item["row"]
        fold = item["fold"]
        patient_hash = item["patient_hash"]
        relative = item["relative"]
        header = item["header"]
        signal = item["signal"]
        if (not header.resolve().is_relative_to(root.resolve())
                or not signal.resolve().is_relative_to(root.resolve())):
            raise ValueError("PTB-XL waveform path escapes its authorized root")
        if (not header.is_file() or not signal.is_file() or header.is_symlink()
                or signal.is_symlink()):
            return None, False
        try:
            signal_spec = _header_summary(header, wfdb_module)
            header_parse_error = None
            excluded_reason = None
        except (OSError, TypeError, ValueError) as exc:
            signal_spec = {}
            header_parse_error = type(exc).__name__
            excluded_reason = "invalid_wfdb_header"
        scp_codes = _read_scp_codes(row["scp_codes"])
        targets, mask = ptbxl_p4_targets(scp_codes)
        record = {
                "task": "pathology",
                "source": "ptbxl",
                "relative_record": relative.as_posix(),
                "identity_hash": _hash_identity("ptbxl", relative.as_posix()),
                "group_hash": patient_hash,
                "patient_hash": patient_hash,
                "fold": fold,
                "signal_sha256": _sha256(signal),
                "split": item["split"],
                "excluded_reason": excluded_reason,
                "targets": targets.astype(int).tolist(),
                "mask": mask.astype(int).tolist(),
                "classes": list(P4_CLASSES),
                **signal_spec,
            }
        if header_parse_error is not None:
            record["header_parse_error_type"] = header_parse_error
        return record, True

    processed = _parallel_map("PTB-XL records", build_pathology_record, prepared_rows)
    result = []
    waveform_count_by_fold = Counter()
    for item, (record, present) in zip(prepared_rows, processed, strict=True):
        if present:
            waveform_count_by_fold[item["fold"]] += 1
        if record is not None:
            result.append(record)
    if any(len(folds) > 1 for folds in patients_by_fold.values()):
        raise ValueError("PTB-XL patient appears in multiple official folds 1..9")
    return result, {
        "metadata_sha256": metadata_hash,
        "scp_statements_sha256": statements_hash,
        "metadata_records_total_including_untouched_fold10": metadata_count,
        "waveforms_accessed_by_official_fold": {str(k): waveform_count_by_fold[k] for k in range(1, 10)},
        "fold10_accessed": False,
        "patient_cross_fold_overlap_folds1_to9": 0,
    }


def _deduplicate(rows: list[dict[str, Any]]) -> None:
    public_evaluation_hashes = {
        row["signal_sha256"]
        for row in rows
        if row["excluded_reason"] == "previous_public_v45_evaluation_record"
    }
    for row in rows:
        if (
            row["task"] == "rhythm"
            and row["excluded_reason"] is None
            and row["signal_sha256"] in public_evaluation_hashes
        ):
            row["excluded_reason"] = "byte_identical_previous_public_v45_evaluation_waveform"

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not row["excluded_reason"]:
            groups[(row["task"], row["signal_sha256"])].append(row)
    for members in groups.values():
        if len(members) < 2:
            continue
        ordered = sorted(
            members,
            key=lambda row: (
                SPLIT_PRIORITY.get(row["split"], 99),
                SOURCE_PRIORITY.get(row["source"], 99),
                row["identity_hash"],
            ),
        )
        for duplicate in ordered[1:]:
            duplicate["excluded_reason"] = "byte_identical_waveform_sha256_duplicate"


def _waveform_qc(
    data_root: Path, rows: list[dict[str, Any]], *, wfdb_module=None, verify_hash: bool = False
) -> dict[str, Any]:
    """Summarize initial-window physical signal properties without filtering records."""
    if wfdb_module is None:
        import wfdb as wfdb_module

    raw_root = data_root / "00_FUENTES_FISICAS_RAW"
    eligible_rows = [row for row in rows if not row["excluded_reason"]]

    def inspect_waveform(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        source_root = raw_root / SOURCE_DIRECTORY_NAMES.get(row["source"], row["source"])
        base = source_root / row["relative_record"]
        try:
            if verify_hash and _sha256(base.with_suffix(".dat")) != row["signal_sha256"]:
                raise WaveformIntegrityError("waveform hash differs from sealed inventory")
            header = wfdb_module.rdheader(str(base))
            sample_count = min(int(header.sig_len), max(1, int(round(10 * header.fs))))
            record = wfdb_module.rdrecord(str(base), sampfrom=0, sampto=sample_count)
            signal = np.asarray(record.p_signal, dtype=np.float64)
            if signal.ndim != 2 or signal.shape[0] == 0 or signal.shape[1] == 0:
                raise ValueError("WFDB returned an empty or non-matrix signal")
            finite = np.isfinite(signal)
            finite_values = np.abs(signal[finite])
            per_lead_flat = []
            for lead in signal.T:
                finite_lead = lead[np.isfinite(lead)]
                per_lead_flat.append(
                    bool(len(finite_lead) and float(np.std(finite_lead)) <= 1e-12)
                )
            units = tuple(sorted({str(unit) for unit in (record.units or [])}))
            sample = {
                "finite_fraction": float(finite.mean()),
                "nonfinite_values": int((~finite).sum()),
                "sample_values": int(finite.size),
                "flat_leads": int(sum(per_lead_flat)),
                "total_leads": len(per_lead_flat),
                "all_zero": bool(len(finite_values) and float(finite_values.max()) <= 1e-12),
                "max_abs_physical_value": (
                    float(finite_values.max()) if len(finite_values) else None
                ),
                "units": ",".join(units) if units else "unknown",
            }
        except WaveformIntegrityError:
            raise
        except (OSError, ValueError, RuntimeError) as exc:
            sample = {"read_error": type(exc).__name__}
        return row["source"], sample

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source, sample in _parallel_map("initial-window waveform QC", inspect_waveform, eligible_rows):
        by_source[source].append(sample)

    result = {}
    for source, samples in sorted(by_source.items()):
        readable = [item for item in samples if "read_error" not in item]
        peaks_by_unit: dict[str, list[float]] = defaultdict(list)
        for item in readable:
            if item["max_abs_physical_value"] is not None:
                peaks_by_unit[item["units"]].append(item["max_abs_physical_value"])
        finite_fractions = [item["finite_fraction"] for item in readable]
        result[source] = {
            "window_seconds_max": 10,
            "records_attempted": len(samples),
            "records_readable": len(readable),
            "read_errors_by_type": dict(sorted(Counter(
                item["read_error"] for item in samples if "read_error" in item
            ).items())),
            "records_with_nonfinite_values": sum(item["nonfinite_values"] > 0 for item in readable),
            "nonfinite_values_total": sum(item["nonfinite_values"] for item in readable),
            "finite_fraction_min": min(finite_fractions) if finite_fractions else None,
            "finite_fraction_median": (
                float(np.median(finite_fractions)) if finite_fractions else None
            ),
            "records_all_zero": sum(item["all_zero"] for item in readable),
            "flat_leads_total": sum(item["flat_leads"] for item in readable),
            "leads_checked_total": sum(item["total_leads"] for item in readable),
            "units_by_record": dict(sorted(Counter(item["units"] for item in readable).items())),
            "max_abs_physical_value_by_unit": {
                units: {
                    "records": len(peaks),
                    "median_record_peak": float(np.median(peaks)),
                    "p95_record_peak": float(np.quantile(peaks, 0.95)),
                    "maximum_record_peak": max(peaks),
                }
                for units, peaks in sorted(peaks_by_unit.items())
            },
            "exclusion_policy": "descriptive_only_no_records_removed_by_this_qc",
        }
    return result


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Any] = {}
    for task in ("rhythm", "pathology"):
        task_rows = [row for row in rows if row["task"] == task]
        by_source: dict[str, Any] = {}
        for source in sorted({row["source"] for row in task_rows}):
            source_rows = [row for row in task_rows if row["source"] == source]
            active = [row for row in source_rows if row["excluded_reason"] is None]
            splits = Counter(row["split"] for row in active)
            exclusions = Counter(row["excluded_reason"] for row in source_rows if row["excluded_reason"])
            classes = active[0]["classes"] if active else []
            support = {}
            for index, name in enumerate(classes):
                observed = [row for row in active if row["mask"][index]]
                positives = sum(row["targets"][index] for row in observed)
                support[name] = {"observed": len(observed), "positive": positives,
                                 "negative_or_control": len(observed) - positives}
            included_specs = [row for row in active if "sample_rate_hz" in row]
            rate_counts = Counter(str(row["sample_rate_hz"]) for row in included_specs)
            lead_counts = Counter(str(row["lead_count"]) for row in included_specs)
            durations = [float(row["duration_seconds"]) for row in included_specs]
            by_source[source] = {
                "candidate_records": len(source_rows),
                "included_records": len(active),
                "included_by_split": dict(sorted(splits.items())),
                "excluded_by_reason": dict(sorted(exclusions.items())),
                "sample_rate_hz_counts": dict(sorted(rate_counts.items())),
                "lead_count_counts": dict(sorted(lead_counts.items())),
                "duration_seconds": {
                    "minimum": min(durations) if durations else None,
                    "median": float(np.median(durations)) if durations else None,
                    "maximum": max(durations) if durations else None,
                },
                "class_support": support,
            }
        counts[task] = by_source
    return counts


def run_audit(data_root: Path, output_dir: Path, repo: Path) -> dict[str, Any]:
    data_root, output_dir = data_root.resolve(), output_dir.resolve()
    if not data_root.is_dir() or output_dir == data_root or output_dir.is_relative_to(data_root):
        raise ValueError("private output must be outside the authorized raw data cache")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    import wfdb

    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir, 0o700)
    rows, prior_eval_receipt = _challenge_records(data_root, config, repo, wfdb_module=wfdb)
    pathology, ptbxl_receipt = _ptbxl_records(data_root, config, wfdb_module=wfdb)
    rows.extend(pathology)
    _deduplicate(rows)
    waveform_qc = _waveform_qc(data_root, rows, wfdb_module=wfdb)

    inventory = output_dir / "private_inventory.json"
    inventory.write_text(json.dumps({"schema": "TITAN_PRIVATE_SPECIALIST_INVENTORY_V1", "rows": rows},
                                    sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.chmod(inventory, 0o600)
    aggregate = _aggregate(rows)
    receipt = {
        "schema": "TITAN_SPECIALIST_INPUT_PREFLIGHT_V1",
        "study_id": config["study_id"],
        "config_sha256": _sha256(CONFIG),
        "private_inventory_sha256": _sha256(inventory),
        "record_level_ids_or_hashes_in_public_receipt": False,
        "data_cache_paths_in_public_receipt": False,
        "ptbxl": ptbxl_receipt,
        "prior_v45_rhythm_evaluation_manifest_audit": prior_eval_receipt,
        "aggregates": aggregate,
        "waveform_qc_initial_window": waveform_qc,
        "duplicate_policy": "raw signal file SHA-256; exact-byte duplicates excluded before splitting; near-duplicate detection not claimed",
        "source_population_status": "partial_physical_cache; only available authorized training-source files included",
        "fold10_used": False,
        "data_test_locked_or_manual_review_queue_used": False,
        "sp_h_or_v3h_used": False,
        "performance_metrics_read_or_computed": False,
    }
    receipt_path = output_dir / "preflight_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(receipt_path, 0o600)
    return receipt


def run_qc_reuse(
    data_root: Path,
    output_dir: Path,
    previous_preflight_dir: Path,
    repo: Path,
    *,
    wfdb_module=None,
) -> dict[str, Any]:
    data_root, output_dir = data_root.resolve(), output_dir.resolve()
    previous_preflight_dir, repo = previous_preflight_dir.resolve(), repo.resolve()
    if (not data_root.is_dir() or output_dir == data_root or output_dir.is_relative_to(data_root)
            or previous_preflight_dir.is_relative_to(data_root)):
        raise ValueError("preflight inputs/outputs must remain outside the authorized raw cache")
    if output_dir == previous_preflight_dir:
        raise ValueError("QC recomputation must use a new output directory")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("QC recomputation output directory must be new or empty")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    config_hash = _sha256(CONFIG)
    repo_config = repo / "configs/specialist_heads/study_20261111_v2.json"
    if not repo_config.is_file() or _sha256(repo_config) != config_hash:
        raise ValueError("repo configuration does not match the script's frozen study configuration")
    source_receipt_path = previous_preflight_dir / "preflight_receipt.json"
    source_inventory_path = previous_preflight_dir / "private_inventory.json"
    source_receipt_hash = _sha256(source_receipt_path)
    source_receipt = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    if (source_receipt.get("schema") != "TITAN_SPECIALIST_INPUT_PREFLIGHT_V1"
            or source_receipt.get("study_id") != config["study_id"]
            or source_receipt.get("config_sha256") != config_hash):
        raise ValueError("source preflight receipt does not match the frozen study configuration")
    inventory_hash = _sha256(source_inventory_path)
    if inventory_hash != source_receipt.get("private_inventory_sha256"):
        raise ValueError("source private inventory hash differs from its sealed receipt")
    inventory = json.loads(source_inventory_path.read_text(encoding="utf-8"))
    if inventory.get("schema") != "TITAN_PRIVATE_SPECIALIST_INVENTORY_V1":
        raise ValueError("unexpected private inventory schema")
    ptbxl_rows = [row for row in inventory["rows"] if row["task"] == "pathology"]
    if not ptbxl_rows or any(row["source"] != "ptbxl" for row in ptbxl_rows):
        raise ValueError("source inventory does not contain the expected PTB-XL rows")
    if wfdb_module is None:
        import wfdb as wfdb_module
    qc = _waveform_qc(data_root, ptbxl_rows, wfdb_module=wfdb_module, verify_hash=True)

    receipt = dict(source_receipt)
    receipt["waveform_qc_initial_window"] = dict(source_receipt["waveform_qc_initial_window"])
    receipt["waveform_qc_initial_window"]["ptbxl"] = qc["ptbxl"]
    receipt["qc_recomputation"] = {
        "source_receipt_sha256": source_receipt_hash,
        "source_private_inventory_sha256": inventory_hash,
        "recomputed_source": "ptbxl",
        "current_waveform_hashes_reverified": True,
        "performance_metrics_read_or_computed": False,
    }

    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir, 0o700)
    inventory_path = output_dir / "private_inventory.json"
    shutil.copyfile(source_inventory_path, inventory_path)
    os.chmod(inventory_path, 0o600)
    if _sha256(inventory_path) != inventory_hash:
        raise ValueError("copied private inventory hash differs from its source")
    receipt_path = output_dir / "preflight_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(receipt_path, 0o600)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True,
                        help="authorized TITAN data-cache root; no other folders are inspected")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="private CEDIA experiment directory outside the raw data cache")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--reuse-qc-from", type=Path,
                        help="reuse a sealed inventory and recompute only PTB-XL waveform QC")
    args = parser.parse_args()
    if args.reuse_qc_from:
        receipt = run_qc_reuse(args.data_root, args.output_dir, args.reuse_qc_from, args.repo)
    else:
        receipt = run_audit(args.data_root, args.output_dir, args.repo)
    print(json.dumps({
        "schema": receipt["schema"], "study_id": receipt["study_id"],
        "private_inventory_sha256": receipt["private_inventory_sha256"],
        "aggregates": receipt["aggregates"], "performance_metrics_read_or_computed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
