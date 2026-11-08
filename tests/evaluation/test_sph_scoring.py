import numpy as np

from titan_v45.evaluation.sph_scoring import score_sph_record
from titan_v45.models.frozen_pathology import P4_CLASSES
from titan_v45.models.frozen_rhythm import P6_CLASSES, P8_CLASSES


class RhythmScorer:
    def __call__(self, windows):
        logits = {
            "P6": np.zeros((len(windows), 8), dtype=np.float32),
            "P8": np.zeros((len(windows), 8), dtype=np.float32),
        }
        logits["P8"][:, 0] = 2
        return logits, np.zeros((len(windows), 6), dtype=np.float32)


class PathologyScorer:
    thresholds = dict.fromkeys(P4_CLASSES, 0.5)

    def __call__(self, windows):
        return [
            ({name: 0.75 for name in P4_CLASSES}, {"AUX": 0.25})
            for _ in windows
        ]


def test_label_free_scorer_emits_all_profiles_and_explicit_fallbacks():
    window = (np.zeros((12, 1250)), np.ones(12, dtype=bool), np.zeros(10))
    thresholds = {
        "P6": dict.fromkeys(P6_CLASSES, 0.9),
        "P8": {name: 0.9 for name in P8_CLASSES},
    }
    result = score_sph_record([window, window], window, RhythmScorer(),
                              PathologyScorer(), thresholds)
    assert result["rhythm_windows"] == 2
    assert not result["profiles"]["P6"]["used_fallback"]
    assert result["profiles"]["P6"]["labels"] == []
    assert result["profiles"]["P8"]["used_fallback"]
    assert result["profiles"]["P6"]["top1"] == P6_CLASSES[0]
    assert result["profiles"]["P4"]["labels"] == list(P4_CLASSES)
    assert result["profiles"]["P8"]["scores"][P8_CLASSES[0]] > 0.8
