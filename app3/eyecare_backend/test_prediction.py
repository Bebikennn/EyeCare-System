"""Quick test of the retrained model prediction"""
import sys
sys.path.insert(0, '.')
from services.ml_predict import predict_risk

# Sample test data
test_data = {
    'Age': 35,
    'Gender': 'Male',
    'BMI': 25,
    'Screen_Time_Hours': 8,
    'Sleep_Hours': 6,
    'Smoker': 0,
    'Alcohol_Use': 0,
    'Diabetes': 0,
    'Hypertension': 0,
    'Family_History_Eye_Disease': 0,
    'Eye_Pain_Frequency': 2,
    'Blurry_Vision_Score': 3,
    'Light_Sensitivity': 2,
    'Eye_Strains_Per_Day': 4,
    'Outdoor_Exposure_Hours': 1,
    'Diet_Score': 3,
    'Water_Intake_Liters': 2,
    'Glasses_Usage': 0,
    'Previous_Eye_Surgery': 0,
    'Physical_Activity_Level': 2
}

print("Testing prediction service...")
result = predict_risk(test_data)

print(f"\nPredicted Disease: {result['predicted_disease']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Risk Level: {result['risk_level']}")
print(f"Risk Score: {result['risk_score']}")

print("\nTop 5 Disease Probabilities:")
sorted_diseases = sorted(result['per_disease_probabilities'].items(), 
                         key=lambda x: x[1], reverse=True)
for i, (disease, prob) in enumerate(sorted_diseases[:5], 1):
    print(f"  {i}. {disease}: {prob:.2%}")

print("\n✓ Model prediction working successfully!")
