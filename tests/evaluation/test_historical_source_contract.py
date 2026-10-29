import ast
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "scripts/cedia/recovery_candidates/backbone_20260629.py"


def test_recovered_backbone_has_exact_historical_inventory_identity():
    rows = json.loads((ROOT / "docs/provenance/source_inventory.json").read_text())["files"]
    expected = next(row for row in rows if row["path"] == "MODEL_CORE/titan_v4_hybrid.py")
    data = ORIGINAL.read_bytes()
    assert len(data) == expected["bytes"] == 9189
    assert hashlib.sha256(data).hexdigest() == expected["sha256"]


def test_every_recovered_forward_body_matches_current_source_without_tuning():
    def forwards(path):
        tree = ast.parse(path.read_bytes())
        return {f"{cls.name}.{node.name}": ast.dump(node, include_attributes=False)
                for cls in tree.body if isinstance(cls, ast.ClassDef)
                for node in cls.body if isinstance(node, ast.FunctionDef)
                and node.name in {"forward", "forward_features"}}

    original = forwards(ORIGINAL)
    current = forwards(ROOT / "src/titan_v45/models/backbone.py")
    assert len(original) == 5
    assert original == current


def test_static_recovery_does_not_claim_waveform_equivalence():
    report = json.loads((ROOT / "outputs/results/revision_20261029/backbone_static_recovery.json").read_text())
    assert report["p4_waveform_equivalence_certified"] is False
    assert report["p4_decision_disagreements_unchanged"] == 166
    assert report["original_morphology_or_event_extractor_recovered"] is False
    assert report["historical_factory_kwargs"]["nhead"] == 10
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == report["recovered_source_sha256"]


def test_original_source_archive_contains_only_exact_inventory_matches():
    report = json.loads((ROOT / "outputs/results/revision_20261029/inventory_matched_source_recovery.json").read_text())
    archive_path = ROOT / report["archive"]["path"]
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == report["archive"]["sha256"]
    recovered = [row for row in report["files"] if row["status"] == "recovered_exact_bytes"]
    assert len(recovered) == report["recovered_exact_files"] == 10
    assert report["declared_original_files"] == 11
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {row["archive_path"] for row in recovered}
        for row in recovered:
            name = Path(row["archive_path"])
            assert not name.is_absolute() and ".." not in name.parts
            data = archive.read(row["archive_path"])
            assert len(data) == row["bytes"]
            assert hashlib.sha256(data).hexdigest() == row["sha256"]


def test_backbone_softmax_is_explicit_in_inventory_verified_original_trainer():
    with zipfile.ZipFile(ROOT / "docs/provenance/recovered-original-sources-20261029.zip") as archive:
        trainer = archive.read("TRAINING/train_v3d_specialists_hpc.py")
    node = next(node for node in ast.parse(trainer).body
                if isinstance(node, ast.FunctionDef) and node.name == "specialist_input_from_base")
    expressions = [ast.unparse(part.value) for part in ast.walk(node) if isinstance(part, ast.Assign)]
    assert "torch.softmax(rhythm_logits.float(), dim=1)" in expressions
    assert "torch.sigmoid(pathology_logits.float())" in expressions


def test_original_twelve_event_extractor_handles_flat_signals_without_new_training():
    import numpy as np
    import torch

    with zipfile.ZipFile(ROOT / "docs/provenance/recovered-original-sources-20261029.zip") as archive:
        trainer = archive.read("TRAINING/train_v3d_specialists_hpc.py")
    names = {"_select_event_peaks_1d", "_signal_event_features_from_batch"}
    functions = [node for node in ast.parse(trainer).body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(functions) == 2
    namespace = {"np": np, "torch": torch, "SIGNAL_EVENT_FEATURE_DIM": 12}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "inventory-verified-event-defs", "exec"), namespace)
    actual = namespace["_signal_event_features_from_batch"](torch.zeros(2, 12, 1250))
    assert actual.shape == (2, 12)
    assert torch.isfinite(actual).all()
