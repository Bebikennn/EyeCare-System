# Risk Score Calculator - Excel Formula Implementation

## Overview
This document explains the risk score calculation based on the original Excel formula for eye disease risk assessment.

## Excel Formula
```excel
=IF(COUNTBLANK($A2:$T2)=COLUMNS($A2:$T2),"",
 (IF($A2<40,0,IF($A2<60,1,IF($A2<70,2,3)))
  + IF($H2=1,3,0)
  + IF($I2=1,2,0)
  + IF($S2=1,2,0)
  + MIN(4,N($L2))
  + IF($M2>=3,1,0)
  + IF($K2>=3,1,0)
  + IF($N2>=3,1,0)
  + IF($D2>=10,2,IF($D2>=6,1,0))
  + IF($O2<=2,1,0)
  + IF(AND($R2=0,N($L2)>=2),1,0)
  + IF($F2=1,1,0)
  + IF($G2>=1,1,0)
 )
)
```

## Column Mapping

| Excel Column | Field Name | Description | Data Type |
|--------------|------------|-------------|-----------|
| A | Age | Patient's age in years | Integer |
| B | BMI | Body Mass Index | Float |
| C | Sleep_Hours | Hours of sleep per night | Float |
| D | Screen_Time_Hours | Daily screen time | Float |
| E | (Reserved) | - | - |
| F | Smoker | Smoking status (0=No, 1=Yes) | Binary |
| G | Alcohol_Use | Alcohol consumption level | Integer |
| H | Diabetes | Diabetic status (0=No, 1=Yes) | Binary |
| I | Hypertension | Hypertension status (0=No, 1=Yes) | Binary |
| J | (Reserved) | - | - |
| K | Light_Sensitivity | Light sensitivity score (0-5) | Integer |
| L | Blurry_Vision_Score | Blurred vision severity (0-5) | Integer |
| M | Eye_Pain_Frequency | Frequency of eye pain (0-5) | Integer |
| N | Eye_Strains_Per_Day | Number of eye strains per day | Integer |
| O | Outdoor_Exposure_Hours | Daily outdoor exposure | Float |
| P | (Reserved) | - | - |
| Q | (Reserved) | - | - |
| R | Glasses_Usage | Uses glasses (0=No, 1=Yes) | Binary |
| S | Family_History_Eye_Disease | Family history (0=No, 1=Yes) | Binary |
| T | Physical_Activity_Level | Physical activity level | Integer |

## Risk Score Breakdown

### Age Factor (0-3 points)
- Age < 40: 0 points
- Age 40-59: 1 point
- Age 60-69: 2 points
- Age ≥ 70: 3 points

### Medical Conditions
- **Diabetes** (H): 3 points
- **Hypertension** (I): 2 points
- **Family History** (S): 2 points

### Eye-Specific Symptoms
- **Blurry Vision Score** (L): MIN(4, score) - capped at 4 points
- **Eye Pain Frequency** (M ≥ 3): 1 point
- **Light Sensitivity** (K ≥ 3): 1 point
- **Eye Strains Per Day** (N ≥ 3): 1 point

### Lifestyle Factors
- **Screen Time** (D):
  - ≥ 10 hours: 2 points
  - 6-9 hours: 1 point
  - < 6 hours: 0 points
- **Outdoor Exposure** (O ≤ 2): 1 point
- **Smoker** (F): 1 point
- **Alcohol Use** (G ≥ 1): 1 point

### Special Condition
- **No Glasses + Blurry Vision** (R=0 AND L≥2): 1 point
  - If patient doesn't wear glasses but has significant blurry vision

## Risk Score Ranges

| Score Range | Risk Level | Description |
|-------------|------------|-------------|
| 0-5 | Low | Minimal eye disease risk |
| 6-10 | Moderate | Moderate risk, monitoring recommended |
| 11+ | High | High risk, medical consultation advised |

## Example Calculation

### Test Case:
- Age: 65 → 2 points
- Diabetes: Yes → 3 points
- Hypertension: No → 0 points
- Family History: Yes → 2 points
- Blurry Vision: 3 → 3 points
- Eye Pain: 4 → 1 point
- Light Sensitivity: 3 → 1 point
- Eye Strains: 2 → 0 points
- Screen Time: 8 hours → 1 point
- Outdoor Exposure: 1 hour → 1 point
- No Glasses + Blurry Vision: Yes → 1 point
- Smoker: Yes → 1 point
- Alcohol: 1 → 1 point

**Total Risk Score: 17 points (High Risk)**

## Python Implementation

The formula is implemented in `risk_score_calculator.py`:

```python
from risk_score_calculator import calculate_risk_score, get_risk_level

# Example usage
patient_data = {
    'Age': 65,
    'Screen_Time_Hours': 8,
    'Diabetes': 1,
    'Hypertension': 0,
    'Blurry_Vision_Score': 3,
    'Eye_Pain_Frequency': 4,
    'Light_Sensitivity': 3,
    'Eye_Strains_Per_Day': 2,
    'Outdoor_Exposure_Hours': 1,
    'Glasses_Usage': 0,
    'Smoker': 1,
    'Alcohol_Use': 1,
    'Family_History_Eye_Disease': 1
}

score = calculate_risk_score(patient_data)
level = get_risk_level(score)

print(f"Risk Score: {score}")
print(f"Risk Level: {level}")
```

## Integration with ML Prediction

The risk score is now integrated into the ML prediction endpoint:

1. **Calculate Risk Score**: Uses the Excel formula to compute risk score
2. **Prepare Features**: Risk score is included as a feature for the LightGBM model
3. **Make Prediction**: Model predicts disease based on all features including risk score
4. **Return Results**: API returns both risk score and predicted disease

### API Response Format
```json
{
  "risk_level": "High",
  "risk_score": 17,
  "predicted_disease": "Dry Eye",
  "confidence": 0.95,
  "model_version": "LightGBM-v2.0",
  "risk_score_breakdown": {
    "calculated_score": 17,
    "risk_level_from_formula": "High",
    "predicted_risk_level": "High"
  },
  "all_predictions": {
    "Dry Eye": 0.95,
    "Myopia": 0.03,
    "Light Sensitivity": 0.02
  }
}
```

## Testing

Run the test script:
```bash
python risk_score_calculator.py
```

Expected output:
```
Test Risk Score: 17
Risk Level: High

Breakdown:
Age (65): 2 points
Diabetes: 3 points
Hypertension: 0 points
Family History: 2 points
Blurry Vision (3): 3 points
Eye Pain (>=3): 1 point
Light Sensitivity (>=3): 1 point
Screen Time (>=6): 1 point
Outdoor Exposure (<=2): 1 point
No Glasses + Blurry Vision: 1 point
Smoker: 1 point
Alcohol: 1 point
```

## Notes

1. **Null/Missing Values**: If any required field is missing or None, the function returns None
2. **Data Validation**: Input values should be validated before passing to the calculator
3. **Maximum Score**: Theoretical maximum is around 20+ points
4. **Minimum Score**: Minimum is 0 points (perfect health profile)
5. **Model Integration**: The risk score is now a feature used by the LightGBM model for disease prediction
