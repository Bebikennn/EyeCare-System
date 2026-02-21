"""
Risk Score Calculator based on Excel formula
Maps Excel columns to assessment data fields
"""

def calculate_risk_score(data):
    """
    Calculate risk score based on health assessment data
    
    Excel Column Mapping:
    A = Age
    B-G = Various health factors
    H = Diabetes
    I = Hypertension  
    J-K = Health metrics
    L = Blurry_Vision_Score
    M = Eye_Pain_Frequency
    N = Eye_Strains_Per_Day
    O = Outdoor_Exposure_Hours
    P-Q = Other factors
    R = Glasses_Usage
    S = Family_History_Eye_Disease
    T = Physical_Activity_Level
    
    Args:
        data: Dictionary with assessment data
        
    Returns:
        int: Calculated risk score (0-20+ range)
    """
    
    # Check if all required fields are present
    required_fields = [
        'Age', 'Diabetes', 'Hypertension', 'Blurry_Vision_Score',
        'Eye_Pain_Frequency', 'Eye_Strains_Per_Day', 'Outdoor_Exposure_Hours',
        'Glasses_Usage', 'Family_History_Eye_Disease', 'Screen_Time_Hours',
        'Smoker', 'Alcohol_Use'
    ]
    
    # If any required field is missing or None, return None
    for field in required_fields:
        if field not in data or data[field] is None:
            return None
    
    risk_score = 0
    
    # Age factor (A2)
    age = int(data.get('Age', 0))
    if age < 40:
        risk_score += 0
    elif age < 60:
        risk_score += 1
    elif age < 70:
        risk_score += 2
    else:
        risk_score += 3
    
    # Diabetes (H2)
    if data.get('Diabetes', 0) == 1:
        risk_score += 3
    
    # Hypertension (I2)
    if data.get('Hypertension', 0) == 1:
        risk_score += 2
    
    # Family History (S2)
    if data.get('Family_History_Eye_Disease', 0) == 1:
        risk_score += 2
    
    # Blurry Vision Score (L2) - MIN(4, value)
    blurry_vision = int(data.get('Blurry_Vision_Score', 0))
    risk_score += min(4, blurry_vision)
    
    # Eye Pain Frequency (M2) - if >= 3
    if int(data.get('Eye_Pain_Frequency', 0)) >= 3:
        risk_score += 1
    
    # Light Sensitivity (K2) - if >= 3
    if int(data.get('Light_Sensitivity', 0)) >= 3:
        risk_score += 1
    
    # Eye Strains Per Day (N2) - if >= 3
    if int(data.get('Eye_Strains_Per_Day', 0)) >= 3:
        risk_score += 1
    
    # Screen Time Hours (D2)
    screen_time = float(data.get('Screen_Time_Hours', 0))
    if screen_time >= 10:
        risk_score += 2
    elif screen_time >= 6:
        risk_score += 1
    
    # Outdoor Exposure (O2) - if <= 2
    if float(data.get('Outdoor_Exposure_Hours', 0)) <= 2:
        risk_score += 1
    
    # Glasses Usage & Blurry Vision interaction (R2 and L2)
    # If no glasses (R2=0) AND Blurry Vision >= 2
    if data.get('Glasses_Usage', 0) == 0 and blurry_vision >= 2:
        risk_score += 1
    
    # Smoker (F2)
    if data.get('Smoker', 0) == 1:
        risk_score += 1
    
    # Alcohol Use (G2) - if >= 1
    if int(data.get('Alcohol_Use', 0)) >= 1:
        risk_score += 1
    
    return risk_score


def get_risk_level(risk_score):
    """
    Determine risk level based on risk score
    
    Args:
        risk_score: Calculated risk score
        
    Returns:
        str: 'Low', 'Moderate', or 'High'
    """
    if risk_score is None:
        return 'Unknown'
    
    if risk_score <= 5:
        return 'Low'
    elif risk_score <= 10:
        return 'Moderate'
    else:
        return 'High'


if __name__ == '__main__':
    # Test the function
    test_data = {
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
    
    score = calculate_risk_score(test_data)
    level = get_risk_level(score)
    
    print(f"Test Risk Score: {score}")
    print(f"Risk Level: {level}")
    print("\nBreakdown:")
    print(f"Age (65): 2 points")
    print(f"Diabetes: 3 points")
    print(f"Hypertension: 0 points")
    print(f"Family History: 2 points")
    print(f"Blurry Vision (3): 3 points")
    print(f"Eye Pain (>=3): 1 point")
    print(f"Light Sensitivity (>=3): 1 point")
    print(f"Screen Time (>=6): 1 point")
    print(f"Outdoor Exposure (<=2): 1 point")
    print(f"No Glasses + Blurry Vision: 1 point")
    print(f"Smoker: 1 point")
    print(f"Alcohol: 1 point")
