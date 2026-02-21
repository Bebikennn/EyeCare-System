from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


CONDITIONS = [
    "Astigmatism",
    "Blurred Vision",
    "Dry Eye",
    "Hyperopia",
    "Light Sensitivity",
    "Myopia",
    "Presbyopia",
]


@dataclass(frozen=True)
class RuleResult:
    probable_condition: str
    triggered_rules: List[str]
    confidence_level: str  # LOW/MED/HIGH


@dataclass(frozen=True)
class ConditionScore:
    score: int
    rules: List[str]


def score_conditions(input_dict: Dict[str, Any]) -> Dict[str, ConditionScore]:
    """Score *all* conditions using the same rule logic as infer_probable_condition.

    This enables the API/UI to show alternative conditions ONLY when they have
    evidence in the user's inputs (i.e., score > 0).
    """

    candidates, _ = _score_candidates(input_dict)
    return {
        name: ConditionScore(score=score, rules=rules)
        for name, score, rules in candidates
    }


def _first_present(input_dict: Dict[str, Any], keys: List[str]) -> Tuple[Optional[str], Any]:
    for k in keys:
        if k in input_dict and input_dict[k] is not None and input_dict[k] != "":
            return k, input_dict[k]
    return None, None


def _as_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _as_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception:
        return None


def _bool01(value: Any) -> Optional[int]:
    v = _as_int(value)
    if v is None:
        return None
    return 1 if v != 0 else 0


def infer_probable_condition(input_dict: Dict[str, Any]) -> RuleResult:
    """Return ONE probable condition (or "Unspecified High Risk") based on pre-condition factors.

    Safety requirements:
    - Only uses lifestyle/history/pre-condition factors.
    - Checks for required columns; skips safely if missing.
    """

    triggered: List[str] = []

    candidates, any_light_proxy_available = _score_candidates(input_dict)

    # Choose best candidate.
    # Tie-breaker: preserve suggested priority order by sorting using CONDITIONS order.
    candidates_sorted = sorted(
        candidates,
        key=lambda t: (t[1], -CONDITIONS.index(t[0]) if t[0] in CONDITIONS else -999),
        reverse=True,
    )

    best_condition, best_score, best_rules = candidates_sorted[0]

    # If the best match is based on weak proxies but not actually triggered, do not force it.
    if best_score <= 0:
        return RuleResult(
            probable_condition="Unspecified High Risk",
            triggered_rules=[],
            confidence_level="LOW",
        )

    # Special handling per prompt: if Light Sensitivity proxies weren't available or didn't trigger,
    # we should not force it.
    if best_condition == "Light Sensitivity" and (not any_light_proxy_available or len(best_rules) == 0):
        return RuleResult(
            probable_condition="Unspecified High Risk",
            triggered_rules=[],
            confidence_level="LOW",
        )

    # Special handling per prompt: if blurred proxy doesn't trigger, don't force.
    if best_condition == "Blurred Vision" and len(best_rules) == 0:
        return RuleResult(
            probable_condition="Unspecified High Risk",
            triggered_rules=[],
            confidence_level="LOW",
        )

    # Confidence heuristic
    # - HIGH: >=3 rule hits or score>=3
    # - MED : score==2
    # - LOW : score==1
    if best_score >= 3 or len(best_rules) >= 3:
        conf = "HIGH"
    elif best_score == 2:
        conf = "MED"
    else:
        conf = "LOW"

    triggered.extend(best_rules)
    return RuleResult(
        probable_condition=best_condition,
        triggered_rules=triggered,
        confidence_level=conf,
    )


def _score_candidates(input_dict: Dict[str, Any]) -> Tuple[List[Tuple[str, int, List[str]]], bool]:
    """Internal scoring helper.

    Returns:
    - candidates: list of (condition, score, rules)
    - any_light_proxy_available: whether any light-sensitivity proxy columns existed
    """

    # Column aliases (dataset uses slightly different names than the prompt)
    age_key, age_val = _first_present(input_dict, ["Age"])
    screen_key, screen_val = _first_present(input_dict, ["Screen_Time_Hours"])
    sleep_key, sleep_val = _first_present(input_dict, ["Sleep_Hours"])
    water_key, water_val = _first_present(input_dict, ["Water_Intake_Liters"])
    glasses_key, glasses_val = _first_present(input_dict, ["Glasses_Usage"])

    outdoor_key, outdoor_val = _first_present(
        input_dict,
        [
            "Outdoor_Time_Hours",  # prompt name
            "Outdoor_Exposure_Hours",  # dataset name
            "Outdoor_Exposure",  # fallback
        ],
    )

    # Optional columns that may not exist
    reading_key, reading_val = _first_present(input_dict, ["Reading_Hours"])
    study_key, study_val = _first_present(input_dict, ["Study_Hours"])

    family_key, family_val = _first_present(
        input_dict,
        [
            "Family_History",  # prompt
            "Family_History_Eye_Disease",  # dataset
        ],
    )

    migraine_key, migraine_val = _first_present(input_dict, ["Migraine_History"])
    uv_key, uv_val = _first_present(
        input_dict,
        [
            "UV_Exposure_Hours",  # prompt
            "Outdoor_Exposure_Hours",  # weak proxy if UV not present
        ],
    )
    sunglasses_key, sunglasses_val = _first_present(input_dict, ["No_Sunglasses"])

    ac_key, ac_val = _first_present(input_dict, ["AC_Exposure"])
    contact_key, contact_val = _first_present(input_dict, ["Contact_Lens_Use"])

    age = _as_float(age_val)
    screen = _as_float(screen_val)
    sleep = _as_float(sleep_val)
    water = _as_float(water_val)
    outdoor = _as_float(outdoor_val)
    reading = _as_float(reading_val)
    study = _as_float(study_val)

    glasses = _bool01(glasses_val)
    family = _bool01(family_val)
    migraine = _bool01(migraine_val)
    ac = _bool01(ac_val)
    contact = _bool01(contact_val)
    no_sunglasses = _bool01(sunglasses_val)
    uv = _as_float(uv_val)

    candidates: List[Tuple[str, int, List[str]]] = []

    # 1) Presbyopia
    presbyopia_score = 0
    presbyopia_rules: List[str] = []
    if age is not None and age >= 40:
        presbyopia_score += 2
        presbyopia_rules.append("Age >= 40")
    if glasses is not None and glasses == 1:
        presbyopia_score += 1
        presbyopia_rules.append("Glasses_Usage == 1")
    if reading is not None and reading >= 2:
        presbyopia_score += 1
        presbyopia_rules.append("Reading_Hours >= 2")
    if study is not None and study >= 3:
        presbyopia_score += 1
        presbyopia_rules.append("Study_Hours >= 3")
    candidates.append(("Presbyopia", presbyopia_score, presbyopia_rules))

    # 2) Myopia
    myopia_score = 0
    myopia_rules: List[str] = []
    if age is not None and age <= 25:
        myopia_score += 2
        myopia_rules.append("Age <= 25")
    if screen is not None and screen >= 6:
        myopia_score += 1
        myopia_rules.append("Screen_Time_Hours >= 6")
    if outdoor is not None and outdoor <= 1.5:
        myopia_score += 1
        myopia_rules.append(f"{outdoor_key} <= 1.5")
    candidates.append(("Myopia", myopia_score, myopia_rules))

    # 3) Dry Eye
    dry_eye_score = 0
    dry_eye_rules: List[str] = []
    if screen is not None and screen >= 6:
        dry_eye_score += 1
        dry_eye_rules.append("Screen_Time_Hours >= 6")
    if sleep is not None and sleep <= 6:
        dry_eye_score += 1
        dry_eye_rules.append("Sleep_Hours <= 6")

    optional_dry_triggers = 0
    if water is not None and water <= 1.5:
        optional_dry_triggers += 1
        dry_eye_rules.append("Water_Intake_Liters <= 1.5")
    if ac is not None and ac == 1:
        optional_dry_triggers += 1
        dry_eye_rules.append("AC_Exposure == 1")
    if contact is not None and contact == 1:
        optional_dry_triggers += 1
        dry_eye_rules.append("Contact_Lens_Use == 1")

    if optional_dry_triggers > 0:
        dry_eye_score += 1

    candidates.append(("Dry Eye", dry_eye_score, dry_eye_rules))

    # 4) Hyperopia
    hyperopia_score = 0
    hyperopia_rules: List[str] = []
    if age is not None and age >= 30:
        hyperopia_score += 1
        hyperopia_rules.append("Age >= 30")
    if glasses is not None and glasses == 1:
        hyperopia_score += 1
        hyperopia_rules.append("Glasses_Usage == 1")
    if outdoor is not None and outdoor <= 1.5:
        hyperopia_score += 1
        hyperopia_rules.append(f"{outdoor_key} <= 1.5")
    candidates.append(("Hyperopia", hyperopia_score, hyperopia_rules))

    # 5) Astigmatism
    astig_score = 0
    astig_rules: List[str] = []
    if glasses is not None and glasses == 1:
        astig_score += 1
        astig_rules.append("Glasses_Usage == 1")
    if screen is not None and screen >= 5:
        astig_score += 1
        astig_rules.append("Screen_Time_Hours >= 5")
    if study is not None and study >= 4:
        astig_score += 1
        astig_rules.append("Study_Hours >= 4")
    if family is not None and family == 1:
        astig_score += 1
        astig_rules.append(f"{family_key} == 1")
    candidates.append(("Astigmatism", astig_score, astig_rules))

    # 6) Light Sensitivity (weak proxy only)
    light_score = 0
    light_rules: List[str] = []
    any_light_proxy_available = any(k is not None for k in [migraine_key, uv_key, sunglasses_key])

    if any_light_proxy_available:
        if migraine is not None and migraine == 1:
            light_score += 1
            light_rules.append("Migraine_History == 1")
        if uv is not None and uv >= 2:
            light_score += 1
            light_rules.append(f"{uv_key} >= 2")
        if no_sunglasses is not None and no_sunglasses == 1:
            light_score += 1
            light_rules.append("No_Sunglasses == 1")

    candidates.append(("Light Sensitivity", light_score, light_rules))

    # 7) Blurred Vision (weak proxy only)
    blurred_score = 0
    blurred_rules: List[str] = []
    if screen is not None and sleep is not None:
        if screen >= 8 and sleep <= 5:
            blurred_score += 1
            blurred_rules.append("Screen_Time_Hours >= 8 AND Sleep_Hours <= 5")
    candidates.append(("Blurred Vision", blurred_score, blurred_rules))

    return candidates, any_light_proxy_available
