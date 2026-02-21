# ===========================================
# Rule-Based Assessment Logic
# ===========================================
def rule_based_assessment(age, screen_time, sleep_hours, diet_quality):
    if screen_time > 6 and sleep_hours < 6:
        return "High Risk"
    elif age > 50 or diet_quality < 2:
        return "Medium Risk"
    else:
        return "Low Risk"
