from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from scripts.evaluation.audit_recovery_bundle import (
    audit_recovery_bundle,
    compare_bundle_to_bundle,
    screen_archive_privacy,
    summarize_bundle_comparison,
    summarize_git_comparison,
)
from scripts.evaluation.recompute_legacy_v4_quarantine import recompute_legacy_v4_quarantine


def _matrix_and_reports() -> dict[str, bytes]:
    labels = [f"C{index}" for index in range(9)]
    diagonal = [100, 90, 80, 70, 60, 30, 20, 6, 5]
    off_diagonal = [30, 30, 30, 30, 30, 20, 15, 15, 11]
    matrix = [[0] * 9 for _ in labels]
    for index, (correct, error) in enumerate(zip(diagonal, off_diagonal, strict=True)):
        matrix[index][index] = correct
        matrix[index][(index + 1) % 9] = error

    total = sum(map(sum, matrix))
    correct = sum(matrix[index][index] for index in range(9))
    f1 = []
    for index in range(9):
        support = sum(matrix[index])
        predicted = sum(row[index] for row in matrix)
        f1.append(2 * matrix[index][index] / (support + predicted))
    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(["true\\pred", *labels])
    for label, row in zip(labels, matrix, strict=True):
        writer.writerow([label, *row])

    external = {
        "class_names": labels,
        "confusion_matrix": matrix,
        "total_evaluated": total,
        "accuracy": correct / total,
        "macro_f1": sum(f1) / 9,
    }
    actions = {
        "accepted_prediction": 107,
        "quarantine_known_boundary": 53,
        "quarantine_rare_rhythm": 0,
        "quarantine_pathology": 0,
        "ood_real": 51,
    }
    cascade = {
        "total_records": total - correct,
        "coverage": 107 / (total - correct),
        "quarantine_rate": 104 / (total - correct),
        "action_counts": actions,
    }
    return {
        "02_CUARENTENA_HISTORICA/primary9_confusion_matrix.csv": csv_buffer.getvalue().encode(),
        "02_CUARENTENA_HISTORICA/primary9_external_report.json": json.dumps(
            external, separators=(",", ":")
        ).encode(),
        "02_CUARENTENA_HISTORICA/cascade_ood_v1_report.json": json.dumps(
            cascade, separators=(",", ":")
        ).encode(),
    }


ROOT = Path(__file__).resolve().parents[2]


def _write_bundle(
    path: Path,
    *,
    add_unsafe_member: bool = False,
    corrupt_inventory_hash: bool = False,
    alternate_inventory_schema: bool = False,
    unsafe_inventory_route: bool = False,
) -> None:
    root = "synthetic-recovery"
    payload = _matrix_and_reports()
    inventory_buffer = io.StringIO(newline="")
    route_field = "ruta" if alternate_inventory_schema else "ruta_relativa"
    inventory_name = (
        "00_LEEME_Y_RESUMEN/INVENTARIO_ZIP.csv"
        if alternate_inventory_schema
        else "00_LEEME_Y_RESUMEN/INVENTARIO_COMPLETO.csv"
    )
    fields = [route_field, "bytes", "sha256"]
    if not alternate_inventory_schema:
        fields.extend(["origen", "tipo", "nivel_evidencia", "transformacion", "sha256_fuente"])
    writer = csv.DictWriter(inventory_buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for index, (relative, data) in enumerate(payload.items()):
        if unsafe_inventory_route and index == 0:
            relative = "../outside.csv"
        row = {
            route_field: relative,
            "bytes": len(data),
            "sha256": (
                "0" * 64
                if corrupt_inventory_hash and index == 0
                else hashlib.sha256(data).hexdigest()
            ),
        }
        if not alternate_inventory_schema:
            row.update(
                {
                    "origen": "synthetic-test",
                    "tipo": "aggregate",
                    "nivel_evidencia": "test-only",
                    "transformacion": "none",
                    "sha256_fuente": "",
                }
            )
        writer.writerow(row)
    inventory = inventory_buffer.getvalue().encode()
    checksummed = {**payload, inventory_name: inventory}
    sums = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {relative}\n"
        for relative, data in checksummed.items()
    ).encode()
    members = {
        **payload,
        inventory_name: inventory,
        "00_LEEME_Y_RESUMEN/SHA256SUMS.txt": sums,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, data in members.items():
            archive.writestr(f"{root}/{relative}", data)
        if add_unsafe_member:
            archive.writestr(f"{root}/../escape.txt", b"not extracted")


def test_recovery_bundle_checks_inventory_checksums_and_crc(tmp_path: Path):
    bundle = tmp_path / "synthetic.zip"
    _write_bundle(bundle)

    report = audit_recovery_bundle(bundle)

    assert report["valid"] is True
    assert report["zip_crc_ok"] is True
    assert report["inventory_rows"] == 3
    assert report["sha256sum_entries"] == 4
    assert report["unsafe_member_count"] == 0
    assert report["duplicate_name_count"] == 0


def test_recovery_bundle_accepts_inventory_zip_route_schema(tmp_path: Path):
    bundle = tmp_path / "inventory-zip-schema.zip"
    _write_bundle(bundle, alternate_inventory_schema=True)

    report = audit_recovery_bundle(bundle)

    assert report["valid"] is True
    assert report["inventory_rows"] == 3
    assert report["sha256sum_entries"] == 4


def test_recovery_bundle_rejects_inventory_path_traversal(tmp_path: Path):
    bundle = tmp_path / "unsafe-inventory-route.zip"
    _write_bundle(bundle, unsafe_inventory_route=True)

    report = audit_recovery_bundle(bundle)

    assert report["valid"] is False
    assert report["error_counts"]["inventory_structure_error_count"] == 1


def test_bundle_audit_rejects_path_traversal(tmp_path: Path):
    bundle = tmp_path / "unsafe.zip"
    _write_bundle(bundle, add_unsafe_member=True)

    report = audit_recovery_bundle(bundle)

    assert report["valid"] is False
    assert report["unsafe_member_count"] == 1


def test_bundle_audit_rejects_inventory_hash_mismatch(tmp_path: Path):
    bundle = tmp_path / "wrong-hash.zip"
    _write_bundle(bundle, corrupt_inventory_hash=True)

    report = audit_recovery_bundle(bundle)

    assert report["valid"] is False
    assert report["error_counts"]["inventory_hash_error_count"] == 1


def test_legacy_error_subset_arithmetic_is_recomputed_without_globalizing_rate(tmp_path: Path):
    bundle = tmp_path / "legacy-v4.zip"
    _write_bundle(bundle)

    report = recompute_legacy_v4_quarantine(bundle)

    assert report["primary9"]["records"] == 672
    assert report["primary9"]["correct_diagonal"] == 461
    assert report["primary9"]["off_diagonal_errors"] == 211
    assert report["routing_on_error_subset_only"]["accepted_prediction"] == 107
    assert report["routing_on_error_subset_only"]["coverage_fraction"] == pytest.approx(107 / 211)
    assert report["routing_on_error_subset_only"]["full_672_record_quarantine_rate"] is None


def test_legacy_recomputation_rejects_inconsistent_actions(tmp_path: Path):
    bundle = tmp_path / "inconsistent.zip"
    _write_bundle(bundle)
    with zipfile.ZipFile(bundle) as archive:
        contents = {info.filename: archive.read(info.filename) for info in archive.infolist()}
    cascade_name = next(name for name in contents if name.endswith("/cascade_ood_v1_report.json"))
    cascade = json.loads(contents[cascade_name])
    cascade["action_counts"]["accepted_prediction"] = 108
    contents[cascade_name] = json.dumps(cascade, separators=(",", ":")).encode()
    _rewrite_bundle_with_updated_manifests(bundle, contents)

    with pytest.raises(ValueError, match="exact partition"):
        recompute_legacy_v4_quarantine(bundle)


def test_privacy_screen_reports_counts_without_exposing_values(tmp_path: Path):
    archive_path = tmp_path / "privacy.zip"
    row_id = "synthetic-record-123"
    token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("bundle/cohort.csv", f"record_id,score\n{row_id},0.5\n")
        archive.writestr("bundle/receipt.txt", f"{token} /home/private/project\n")
        archive.writestr("bundle/metadata.json", '{"path":"/CEDIA_PROJECT/receipt.json"}')

    result = screen_archive_privacy(archive_path)

    assert result["csv_headers_with_record_or_patient_id_fields"] == 1
    assert result["common_private_key_or_token_markers"] == 1
    assert result["source_receipts_contain_internal_paths"] is True
    assert row_id not in json.dumps(result)
    assert token not in json.dumps(result)


def test_privacy_screen_detects_absolute_paths_in_json_values(tmp_path: Path):
    archive_path = tmp_path / "json-path.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("bundle/receipt.json", '{"source":"/CEDIA_PROJECT/archive/item.json"}')

    result = screen_archive_privacy(archive_path)

    assert result["source_receipts_contain_internal_paths"] is True


def test_git_comparison_summary_counts_matches_without_paths():
    payloads = [
        ("package/a.csv", "same"),
        ("package/b.csv", "new"),
        ("package/c.csv", "other"),
    ]
    tracked = [
        ("data/a.csv", "same"),
        ("docs/b.csv", "old"),
    ]

    report = summarize_git_comparison(payloads, tracked)

    assert report == {
        "payload_count": 3,
        "byte_identical_to_any_tracked_file_count": 1,
        "exact_relative_path_and_bytes_count": 0,
        "nonidentical_payload_count": 2,
        "same_basename_different_bytes_count": 1,
        "tracked_file_count": 2,
    }
    assert "package/" not in json.dumps(report)


def test_bundle_comparison_summary_counts_hash_matches_without_paths():
    report = summarize_bundle_comparison(
        [("first/a.csv", "same"), ("first/b.csv", "same"), ("first/c.csv", "new")],
        [("second/a.csv", "same"), ("second/b.csv", "other")],
    )

    assert report == {
        "first_payload_count": 3,
        "second_payload_count": 2,
        "byte_identical_member_pairs": 1,
        "first_members_matching_second_count": 2,
        "second_members_matching_first_count": 1,
        "exact_relative_path_and_bytes_count": 0,
    }
    assert "first/" not in json.dumps(report)
    assert "second/" not in json.dumps(report)


def test_bundle_comparison_validates_archives_and_omits_member_paths(tmp_path: Path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    _write_bundle(first)
    _write_bundle(second)

    report = compare_bundle_to_bundle(first, second)

    assert report["first_payload_count"] == 4
    assert report["second_payload_count"] == 4
    assert report["byte_identical_member_pairs"] == 4
    assert report["exact_relative_path_and_bytes_count"] == 4
    assert "synthetic-recovery/" not in json.dumps(report)


def test_reviewer_matrix_counts_and_bounded_updates_are_consistent():
    source = json.loads(
        (ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.json").read_text(encoding="utf-8")
    )
    technical = json.loads(
        (ROOT / "docs/reviewer_closure/REVIEWER_15_TECHNICAL_FINAL_MATRIX.json").read_text(
            encoding="utf-8"
        )
    )
    source_items = source["items"]
    assert len(source_items) == source["counts"]["total"] == 48
    assert len({item["id"] for item in source_items}) == 48
    audit_items = {item["id"]: item for item in source_items if item["id"].startswith("A-")}
    assert len(audit_items) == source["counts"]["project_audit"] == 12
    assert source["counts"]["peer_review"] == 36

    audit_updates = source["recovery_zip_internal_audit_update"]
    assert audit_updates["source_statuses_unchanged"] is True
    assert {item["id"] for item in audit_updates["items"]} == set(audit_items)
    for update in audit_updates["items"]:
        assert update["source_status"] == audit_items[update["id"]]["technical_status"]

    technical_items = {item["id"]: item for item in technical["items"]}
    zip_updates = technical["recovery_zip_reconciliation"]["item_updates"]
    assert len(technical_items) == len(zip_updates) == 15
    assert {item["id"] for item in zip_updates} == set(technical_items)
    for update in zip_updates:
        item = technical_items[update["id"]]
        assert update["overall_status_unchanged"] == (
            f"{item['technical_status']} / {item['reviewer_satisfaction']}"
        )
    assert technical["counts"]["reviewer_satisfaction"] == {
        "PARTIALLY_ADDRESSED": 12,
        "NOT_SATISFIED": 3,
    }
    assert technical["counts"]["manuscript_edited"] is False


def test_selected_cohort_denominator_relationships_remain_consistent():
    def record_ids(relative_path: str) -> set[str]:
        with (ROOT / relative_path).open(encoding="utf-8", newline="") as stream:
            return {row["record_id"] for row in csv.DictReader(stream)}

    p8 = record_ids("data/manifests/external_dev/rhythm_primary8_records.csv")
    p6 = record_ids("data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv")
    with (ROOT / "data/manifests/external_dev/pathology_primary4_panels.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        p4_rows = list(csv.DictReader(stream))
    p4 = {row["record_id"] for row in p4_rows}

    assert len(p6) == 1643 and p6 <= p8
    assert len(p8) == 2193
    assert len(p4_rows) == 962 and len(p4) == 733
    assert not (p8 & p4)
    assert len(p8 | p4) == 2926


def _rewrite_bundle_with_updated_manifests(path: Path, contents: dict[str, bytes]) -> None:
    root = "synthetic-recovery"
    prefix = root + "/"
    payload = {
        name[len(prefix) :]: data
        for name, data in contents.items()
        if name.startswith(prefix)
        and not name.endswith("/INVENTARIO_COMPLETO.csv")
        and not name.endswith("/SHA256SUMS.txt")
    }
    inventory_buffer = io.StringIO(newline="")
    fields = [
        "ruta_relativa",
        "bytes",
        "sha256",
        "origen",
        "tipo",
        "nivel_evidencia",
        "transformacion",
        "sha256_fuente",
    ]
    writer = csv.DictWriter(inventory_buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for relative, data in payload.items():
        writer.writerow(
            {
                "ruta_relativa": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "origen": "synthetic-test",
                "tipo": "aggregate",
                "nivel_evidencia": "test-only",
                "transformacion": "none",
                "sha256_fuente": "",
            }
        )
    inventory = inventory_buffer.getvalue().encode()
    checksummed = {**payload, "00_LEEME_Y_RESUMEN/INVENTARIO_COMPLETO.csv": inventory}
    sums = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {relative}\n"
        for relative, data in checksummed.items()
    ).encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, data in payload.items():
            archive.writestr(prefix + relative, data)
        archive.writestr(prefix + "00_LEEME_Y_RESUMEN/INVENTARIO_COMPLETO.csv", inventory)
        archive.writestr(prefix + "00_LEEME_Y_RESUMEN/SHA256SUMS.txt", sums)
