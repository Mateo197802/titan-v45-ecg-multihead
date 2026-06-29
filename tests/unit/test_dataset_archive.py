from __future__ import annotations

import csv
from pathlib import Path

from titan_v45.artifacts.dataset_archive import materialize_external_development_package


def test_materialize_external_package_copies_companions_and_sanitizes_paths(
    tmp_path: Path,
) -> None:
    source = tmp_path / "private" / "records" / "A0001"
    source.parent.mkdir(parents=True)
    source.with_suffix(".hea").write_text("A0001 1 125 10\nA0001.dat 16 1/mV 0 0 0 0 I\n")
    source.with_suffix(".dat").write_bytes(b"signal")
    manifest = tmp_path / "input.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["record_id", "record_base", "header_path", "source", "dx_codes"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_id": "A0001",
                "record_base": str(source),
                "header_path": str(source.with_suffix(".hea")),
                "source": "Example Source",
                "dx_codes": "123",
            }
        )
    output = tmp_path / "package"
    report = materialize_external_development_package([manifest], output)
    assert report.unique_records == 1
    public_manifest = output / "manifests" / "input.csv"
    text = public_manifest.read_text(encoding="utf-8")
    assert str(tmp_path) not in text
    assert "records/example-source/A0001/A0001" in text
    assert (output / "records" / "example-source" / "A0001" / "A0001.hea").is_file()
    assert (output / "records" / "example-source" / "A0001" / "A0001.dat").is_file()
    assert (output / "package-manifest.json").is_file()


def test_materialize_external_package_includes_dataset_license_files(tmp_path: Path) -> None:
    source = tmp_path / "private" / "records" / "A0002"
    source.parent.mkdir(parents=True)
    source.with_suffix(".hea").write_text("A0002 1 125 10\nA0002.dat 16 1/mV 0 0 0 0 I\n")
    source.with_suffix(".dat").write_bytes(b"signal")
    manifest = tmp_path / "input.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "record_base", "source"])
        writer.writeheader()
        writer.writerow({"record_id": "A0002", "record_base": str(source), "source": "PTB-XL"})
    license_file = tmp_path / "PTB-XL-CC-BY-4.0.md"
    license_file.write_text("CC BY 4.0 citation text\n", encoding="utf-8")

    output = tmp_path / "package"
    materialize_external_development_package([manifest], output, license_files=[license_file])

    copied_license = output / "licenses" / "PTB-XL-CC-BY-4.0.md"
    assert copied_license.read_text(encoding="utf-8") == "CC BY 4.0 citation text\n"
    manifest_text = (output / "package-manifest.json").read_text(encoding="utf-8")
    assert "licenses/PTB-XL-CC-BY-4.0.md" in manifest_text
