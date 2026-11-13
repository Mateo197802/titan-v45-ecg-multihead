import importlib.util
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "specialist_extract_features", ROOT / "scripts/specialist_experiments/extract_features.py"
)
extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)


def test_bounded_parallel_reader_preserves_input_order():
    def delayed_identity(value):
        time.sleep((4 - value) * 0.005)
        return value

    with ThreadPoolExecutor(max_workers=4) as executor:
        actual = list(extractor._bounded_ordered_map(
            executor, delayed_identity, range(5), limit=4
        ))

    assert actual == list(range(5))


def test_bounded_parallel_reader_rejects_zero_pending_limit():
    with ThreadPoolExecutor(max_workers=1) as executor:
        try:
            list(extractor._bounded_ordered_map(executor, lambda item: item, [], limit=0))
        except ValueError as error:
            assert "positive" in str(error)
        else:
            raise AssertionError("zero pending limit must be rejected")


def test_rhythm_reader_passes_suffixless_signal_path(monkeypatch, tmp_path):
    signal_path = tmp_path / "record.mat"
    monkeypatch.setattr(extractor, "_signal_path", lambda source, relative: signal_path)
    monkeypatch.setattr(extractor, "_sha256", lambda path: "expected")
    observed = {}

    def prepare(record_path, morphology):
        observed["record_path"] = record_path
        observed["morphology"] = morphology
        return ["prepared-window"]

    monkeypatch.setattr(extractor, "prepare_rhythm_record", prepare)
    result = extractor._read_rhythm_record(
        tmp_path, "morphology", 3,
        {"source": "source", "relative_record": "record", "signal_sha256": "expected"},
    )

    assert result == (3, ["prepared-window"], None)
    assert observed == {"record_path": tmp_path / "record", "morphology": "morphology"}
