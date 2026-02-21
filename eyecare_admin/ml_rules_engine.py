"""Rule-based probable condition inference (Stage 2).

IMPORTANT:
- This is ONLY executed when the Stage-1 model predicts HIGH overall risk.
- It uses only pre-condition / lifestyle factors (no symptom-derived features).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RuleResult:
    probable_condition: str
    triggered_rules: list[str]
    confidence_level: str


def infer_probable_condition(features: Mapping[str, Any]) -> RuleResult:
    """Infer a probable condition from a single user's feature dict.

    Returns:
        RuleResult with probable_condition and triggered_rules.

    Notes:
        If no rules match, returns "Unspecified High Risk".
    """

    def get_float(key: str, default: float | None = None) -> float | None:
        if key not in features:
            return default
        val = features.get(key)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except Exception:
            return default

    def get_int(key: str, default: int | None = None) -> int | None:
        f = get_float(key, None)
        if f is None:
            return default
        try:
            return int(round(f))
        except Exception:
            return default

    triggered: list[str] = []

    age = get_int("Age")
    screen_time = get_float("Screen_Time_Hours")
    outdoor = get_float("Outdoor_Exposure_Hours")
    water = get_float("Water_Intake_Liters")
    sleep = get_float("Sleep_Hours")
    diet = get_float("Diet_Score")
    glasses = get_int("Glasses_Usage")
    prev_surgery = get_int("Previous_Eye_Surgery")

    # Rule priorities chosen to align with plausible risk-factor correlations.

    # Presbyopia: strongly age-related
    if age is not None and age >= 45:
        triggered.append("Age>=45 -> Presbyopia")
        return RuleResult("Presbyopia", triggered, "medium")

    # Myopia: higher screen time + low outdoor exposure, and/or glasses usage
    if (
        (screen_time is not None and outdoor is not None and screen_time >= 7 and outdoor <= 2)
        or (glasses is not None and glasses == 1 and age is not None and age < 45)
    ):
        if screen_time is not None and outdoor is not None and screen_time >= 7 and outdoor <= 2:
            triggered.append("Screen_Time_Hours>=7 and Outdoor_Exposure_Hours<=2 -> Myopia")
        if glasses is not None and glasses == 1 and age is not None and age < 45:
            triggered.append("Glasses_Usage==1 and Age<45 -> Myopia")
        return RuleResult("Myopia", triggered, "medium")

    # Dry Eye: low water intake, low sleep, low diet score
    dry_eye_hits = 0
    if water is not None and water < 1.5:
        dry_eye_hits += 1
        triggered.append("Water_Intake_Liters<1.5 -> Dry Eye")
    if sleep is not None and sleep < 6:
        dry_eye_hits += 1
        triggered.append("Sleep_Hours<6 -> Dry Eye")
    if diet is not None and diet <= 2:
        dry_eye_hits += 1
        triggered.append("Diet_Score<=2 -> Dry Eye")

    if dry_eye_hits >= 2:
        return RuleResult("Dry Eye", triggered, "medium")

    # Hyperopia: weak proxy (older-ish, low glasses usage)
    if age is not None and 35 <= age < 45 and (glasses is None or glasses == 0):
        triggered.append("35<=Age<45 and Glasses_Usage!=1 -> Hyperopia")
        return RuleResult("Hyperopia", triggered, "low")

    # Astigmatism: very weak proxy (prior surgery can correlate with vision issues)
    if prev_surgery is not None and prev_surgery == 1:
        triggered.append("Previous_Eye_Surgery==1 -> Astigmatism (weak proxy)")
        return RuleResult("Astigmatism", triggered, "low")

    return RuleResult("Unspecified High Risk", triggered, "low")
