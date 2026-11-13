"""Create a sanitized, aggregate-only publication package for the SPH PAC probe."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_PROTOCOL_COMMIT = "73a167f51c35b10a825854a9d0f6591eb5754e4c"
EXPECTED_PROTOCOL_CONFIG_SHA256 = "2a3f81fb0304030b9738c79fba5507a750452b0d1a89fcaa0980d5adf8e6b921"
EXPECTED_EXECUTION_AGGREGATE_SHA256 = "702022c4ee1e0672649dd732777c357952119fa268cee47f9309ad273765c54a"
EXPECTED_EXECUTION_RECEIPT_SHA256 = "a25466470b1fcbde4966c8b98db23cee342e5e22026f98148ee69535b0b85071"
EXPECTED_SOURCE_RECORDS = 25_770
EXPECTED_LABEL_CODE_AUDIT = {
    "records": 25_770,
    "code_30_records": 539,
    "code_31_records": 4,
    "records_with_both_codes": 1,
    "code_31_only_records": 3,
    "code_30_only_records": 538,
    "neither_code_records": 25_228,
    "code_30_description": "Atrial premature complex(es)",
    "code_31_description": "Atrial premature complexes, nonconducted",
}
PUBLIC_TARGET = (
    "SPH primary code 30 present; code 31-only records remain included as code-30-absent "
    "target-negative observations, not clinical negatives; all technically eligible ECGs remain"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def summarize_label_policy(source_directory: Path) -> dict:
    """Return only label-code counts; never serialize ECG or patient identities."""
    source_directory = Path(source_directory)
    with (source_directory / "code.csv").open(encoding="utf-8-sig", newline="") as stream:
        dictionary_reader = csv.DictReader(stream)
        if not {"Category", "Code", "Description"}.issubset(dictionary_reader.fieldnames or ()):
            raise ValueError("SPH dictionary lacks required columns")
        primary, modifiers = {}, set()
        for row in dictionary_reader:
            code = int(row["Code"])
            description = row["Description"].strip()
            if not description or code in primary or code in modifiers:
                raise ValueError("SPH dictionary contains a duplicate code or empty description")
            if row["Category"] == "Modifier":
                modifiers.add(code)
            else:
                primary[code] = description
    with (source_directory / "metadata.csv").open(encoding="utf-8-sig", newline="") as stream:
        metadata_reader = csv.DictReader(stream)
        required = {"ECG_ID", "AHA_Code", "Patient_ID", "N", "Age", "Sex", "Date"}
        if not required.issubset(metadata_reader.fieldnames or ()):
            raise ValueError("SPH metadata lacks required columns")
        seen_ids = set()
        code_sets = []
        for row in metadata_reader:
            record_id = row["ECG_ID"]
            if (not re.fullmatch(r"A[0-9]{5}", record_id) or record_id in seen_ids
                    or not row["Patient_ID"].strip()):
                raise ValueError("SPH metadata contains a duplicate or invalid record row")
            seen_ids.add(record_id)
            if int(row["N"]) < 1:
                raise ValueError("SPH metadata contains an invalid sample count")
            codes = set()
            for statement in row["AHA_Code"].split(";"):
                tokens = [int(token) for token in statement.split("+")]
                core, extra = tokens[0], tokens[1:]
                if (core not in primary or len(set(extra)) != len(extra)
                        or any(code not in modifiers for code in extra)):
                    raise ValueError("SPH metadata contains an invalid primary code or modifier")
                codes.add(core)
            code_sets.append(codes)

    if 30 not in primary or 31 not in primary:
        raise ValueError("SPH dictionary lacks primary codes 30 and 31")
    if primary[30] != EXPECTED_LABEL_CODE_AUDIT["code_30_description"]:
        raise ValueError("SPH code 30 description differs from the frozen definition")
    if primary[31] != EXPECTED_LABEL_CODE_AUDIT["code_31_description"]:
        raise ValueError("SPH code 31 description differs from the frozen definition")

    code_30 = sum(30 in codes for codes in code_sets)
    code_31 = sum(31 in codes for codes in code_sets)
    both = sum(30 in codes and 31 in codes for codes in code_sets)
    code_31_only = sum(31 in codes and 30 not in codes for codes in code_sets)
    code_30_only = sum(30 in codes and 31 not in codes for codes in code_sets)
    neither = sum(30 not in codes and 31 not in codes for codes in code_sets)
    audit = {
        "records": len(code_sets),
        "code_30_records": code_30,
        "code_31_records": code_31,
        "records_with_both_codes": both,
        "code_31_only_records": code_31_only,
        "code_30_only_records": code_30_only,
        "neither_code_records": neither,
        "code_30_description": primary[30],
        "code_31_description": primary[31],
    }
    if audit["records"] != EXPECTED_SOURCE_RECORDS:
        raise ValueError("SPH source record count differs from the frozen protocol")
    if code_30_only + code_31_only + both + neither != len(code_sets):
        raise ValueError("SPH code 30/31 categories do not partition the source records")
    if audit != EXPECTED_LABEL_CODE_AUDIT:
        raise ValueError("SPH code 30/31 counts differ from the verified source audit")
    return audit


def normalize_execution_artifacts(
    raw_aggregate: dict,
    raw_receipt: dict,
    label_audit: dict,
    *,
    execution_aggregate_sha256: str,
    execution_receipt_sha256: str,
) -> tuple[dict, dict]:
    """Preserve measured values while replacing the broad execution receipt with a scoped one."""
    if execution_aggregate_sha256 != EXPECTED_EXECUTION_AGGREGATE_SHA256:
        raise ValueError("execution aggregate SHA-256 is not the frozen CEDIA output")
    if execution_receipt_sha256 != EXPECTED_EXECUTION_RECEIPT_SHA256:
        raise ValueError("execution receipt SHA-256 is not the frozen CEDIA output")
    if raw_aggregate.get("schema") != "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V1":
        raise ValueError("unexpected source execution aggregate schema")
    if raw_receipt.get("schema") != "TITAN_V45_SPH_PAC_PROBE_RECEIPT_V1":
        raise ValueError("unexpected source execution receipt schema")
    if raw_receipt.get("protocol_commit") != EXPECTED_PROTOCOL_COMMIT:
        raise ValueError("source execution does not use the frozen protocol commit")
    if raw_receipt.get("protocol_config_sha256") != EXPECTED_PROTOCOL_CONFIG_SHA256:
        raise ValueError("source execution protocol configuration SHA-256 mismatch")
    if raw_receipt.get("public_aggregate_sha256") != execution_aggregate_sha256:
        raise ValueError("source execution receipt does not bind the measured aggregate")
    if label_audit != EXPECTED_LABEL_CODE_AUDIT:
        raise ValueError("label-code audit differs from the verified source audit")

    aggregate = json.loads(json.dumps(raw_aggregate))
    aggregate["schema"] = "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V2"
    aggregate["target"] = PUBLIC_TARGET
    aggregate["label_code_audit"] = label_audit
    aggregate_sha256 = hashlib.sha256(_json_bytes(aggregate)).hexdigest()

    receipt = {
        "schema": "TITAN_V45_SPH_PAC_PUBLICATION_RECEIPT_V1",
        "status": "exploratory_nonclinical_nonindependent",
        "artifact_scope": "PAC probe public artifacts only",
        "public_aggregate_sha256": aggregate_sha256,
        "source_execution_aggregate_sha256": execution_aggregate_sha256,
        "source_execution_receipt_sha256": execution_receipt_sha256,
        "publication_normalizer_sha256": _sha256_file(Path(__file__).resolve()),
        "protocol_commit": raw_receipt["protocol_commit"],
        "protocol_config_sha256": raw_receipt["protocol_config_sha256"],
        "source_sha256": raw_receipt["source_sha256"],
        "v3f_checkpoint_sha256": raw_receipt["v3f_checkpoint_sha256"],
        "embedding_archive_sha256": raw_receipt["embedding_archive_sha256"],
        "embedding_receipt_sha256": raw_receipt["embedding_receipt_sha256"],
        "dependency_archive_sha256": raw_receipt["dependency_archive_sha256"],
        "runtime": raw_receipt["runtime"],
        "labels_used_for_head_fitting": raw_receipt["labels_used_for_head_fitting"],
        "threshold_or_model_tuning_on_holdout": raw_receipt[
            "threshold_or_model_tuning_on_holdout"
        ],
        "mimic_data_consulted": raw_receipt["mimic_data_consulted"],
        "pac_row_level_data_in_public_artifacts": False,
        "pac_individual_identifiers_in_public_artifacts": False,
        "pac_probe_weights_in_public_artifacts": False,
        "slurm_job_id": raw_receipt["slurm_job_id"],
        "metric_validation": {
            "confusion_derived_metrics_recomputed": True,
            "score_metrics_recomputed_from_row_scores": False,
            "bootstrap_intervals_recomputed_from_row_scores": False,
            "score_metrics_and_bootstrap_bound_to_cedia_execution_digests": True,
        },
    }
    return aggregate, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--raw-aggregate", type=Path, required=True)
    parser.add_argument("--raw-receipt", type=Path, required=True)
    parser.add_argument("--protocol-config", type=Path,
                        default=ROOT / "configs/external_validation/pac_v3f_embedding_probe.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    config_bytes = args.protocol_config.read_bytes()
    if hashlib.sha256(config_bytes).hexdigest() != EXPECTED_PROTOCOL_CONFIG_SHA256:
        raise ValueError("protocol configuration does not match the frozen digest")
    config = json.loads(config_bytes)
    for name in ("code.csv", "metadata.csv"):
        if _sha256_file(args.source_dir / name) != config["source"]["sha256"][name]:
            raise ValueError(f"SPH source {name} does not match the frozen digest")

    raw_aggregate_bytes = args.raw_aggregate.read_bytes()
    raw_receipt_bytes = args.raw_receipt.read_bytes()
    raw_aggregate = json.loads(raw_aggregate_bytes)
    raw_receipt = json.loads(raw_receipt_bytes)
    aggregate, receipt = normalize_execution_artifacts(
        raw_aggregate,
        raw_receipt,
        summarize_label_policy(args.source_dir),
        execution_aggregate_sha256=hashlib.sha256(raw_aggregate_bytes).hexdigest(),
        execution_receipt_sha256=hashlib.sha256(raw_receipt_bytes).hexdigest(),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    aggregate_path = args.output_dir / "pac_probe_aggregate.json"
    receipt_path = args.output_dir / "pac_probe_receipt.json"
    aggregate_path.write_bytes(_json_bytes(aggregate))
    receipt_path.write_bytes(_json_bytes(receipt))
    print(json.dumps({
        "aggregate_sha256": _sha256_file(aggregate_path),
        "receipt_sha256": _sha256_file(receipt_path),
        "label_code_audit": aggregate["label_code_audit"],
        "output_files": [aggregate_path.name, receipt_path.name],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
