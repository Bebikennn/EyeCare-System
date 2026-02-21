"""Test assessment submission"""
import requests
import json

url = "http://localhost:5000/api/assessment/submit"
data = {
    "user_id": "test-user-001",
    "Age": 21,
    "Gender": "Male",
    "BMI": 34.0,
    "Screen_Time_Hours": 4.0,
    "Sleep_Hours": 4.0,
    "Smoker": "Yes",
    "Alcohol_Use": "Yes",
    "Diabetes": "Yes",
    "Hypertension": "No",
    "Family_History_Eye_Disease": "Yes",
    "Eye_Pain_Frequency": 5,
    "Blurry_Vision_Score": 10,
    "Light_Sensitivity": "Yes",
    "Eye_Strains_Per_Day": 3,
    "Outdoor_Exposure_Hours": 3.0,
    "Diet_Score": 10,
    "Water_Intake_Liters": 2.0,
    "Glasses_Usage": "Yes",
    "Previous_Eye_Surgery": "Yes",
    "Physical_Activity_Level": "Moderate"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
