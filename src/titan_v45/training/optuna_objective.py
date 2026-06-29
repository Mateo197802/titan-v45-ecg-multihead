from __future__ import annotations


def composite_primary_score(
    *,
    primary8_macro_f1: float,
    primary4_macro_f1: float,
    missing_primary8: int = 0,
    missing_primary4: int = 0,
    missing_class_penalty: float = 0.05,
) -> float:
    score = 0.60 * float(primary8_macro_f1) + 0.40 * float(primary4_macro_f1)
    missing = int(missing_primary8) + int(missing_primary4)
    return round(score - float(missing_class_penalty) * missing, 12)
