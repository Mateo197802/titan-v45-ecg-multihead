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
