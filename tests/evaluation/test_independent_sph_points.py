import pytest

from scripts.external_validation.independent_sph_points import points
from titan_v45.evaluation.revision_report import binary_metrics


def test_independent_points_match_existing_metric_implementation_with_ties():
    rows = [(0, 0, 0.1), (1, 1, 0.8), (0, 1, 0.8), (1, 0, 0.3), (1, 1, 0.7)]
    independent = points(rows)
    reference = binary_metrics([r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows])
    for name, value in independent.items():
        assert value == pytest.approx(reference[name])


def test_independent_points_handle_absent_positive_and_invalid_score():
    assert points([(0, 0, 0.1)])["auroc"] is None
    assert points([(0, 0, 0.1)])["average_precision"] is None
    with pytest.raises(ValueError, match="invalid"):
        points([(1, 1, 1.1)])
