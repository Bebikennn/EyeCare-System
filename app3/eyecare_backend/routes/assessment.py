# ===============================
# Assessment Routes
# ===============================
from flask import Blueprint, request, jsonify
from services.db import get_connection
from services.ml_predict import predict_risk, get_recommendations
from ml_models.rules_engine import CONDITIONS, score_conditions
from datetime import datetime, timezone
import uuid
import json

assessment_bp = Blueprint("assessment", __name__)


def _to_01(value):
    return 1 if value in ["Yes", True, 1, "1", "true", "True"] else 0


def _physical_activity_to_level(value):
    """Dataset typically uses 1-4 (sometimes blank). Accept strings too."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        v = value.strip().lower()
        mapping = {
            "low": 1,
            "light": 1,
            "moderate": 2,
            "medium": 2,
            "high": 3,
            "very high": 4,
        }
        if v in mapping:
            return mapping[v]
        try:
            return int(float(v))
        except Exception:
            return None
    return None


def _clamp01(x: float) -> float:
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return float(x)


def _parse_json_maybe(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def _looks_like_legacy_one_hot(per_disease: dict, predicted_disease) -> bool:
    if not isinstance(per_disease, dict) or not per_disease:
        return False
    if not predicted_disease or predicted_disease not in per_disease:
        return False
    # Legacy format was exactly 1.0 for predicted, 0.0 for others.
    try:
        pred_v = float(per_disease.get(predicted_disease, 0.0))
    except Exception:
        return False
    if abs(pred_v - 1.0) > 1e-6:
        return False

    for k, v in per_disease.items():
        if k == predicted_disease:
            continue
        if k == "Other / Unspecified":
            # New format may include this key.
            return False
        try:
            if abs(float(v)) > 1e-6:
                return False
        except Exception:
            return False
    return True


def _recompute_per_disease_probabilities(*, assessment_data: dict, predicted_disease: str, confidence_score: float) -> dict:
    """Recompute per-condition probabilities for legacy stored records.

    Uses stored assessment_data + stored confidence_score (0-100) and the same
    rule scoring used in live predictions.
    """
    predicted_p = _clamp01(float(confidence_score) / 100.0)
    remainder = max(0.0, 1.0 - predicted_p)

    scores = score_conditions(assessment_data)
    other_candidates = [
        c
        for c in CONDITIONS
        if c != predicted_disease and c in scores and scores[c].score > 0
    ]
    other_score_sum = sum(scores[c].score for c in other_candidates)

    per_condition = {c: 0.0 for c in CONDITIONS}
    if predicted_disease in per_condition:
        per_condition[predicted_disease] = predicted_p

    if remainder > 0 and other_score_sum > 0:
        for c in other_candidates:
            per_condition[c] = remainder * (scores[c].score / other_score_sum)
    elif remainder > 0:
        per_condition["Other / Unspecified"] = remainder

    return per_condition

@assessment_bp.route("/api/assessment/submit", methods=["POST"])
def submit_assessment():
    """
    Submit assessment data and get ML prediction.
    Expects JSON body with assessment fields matching dataset features.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        # Extract assessment data
        assessment_data = {
            "Age": data.get("Age", 0),
            "Gender": data.get("Gender", "Male"),
            "BMI": data.get("BMI", 0),
            "Screen_Time_Hours": data.get("Screen_Time_Hours", 0),
            "Sleep_Hours": data.get("Sleep_Hours", 7),
            "Smoker": _to_01(data.get("Smoker")),
            "Alcohol_Use": _to_01(data.get("Alcohol_Use")),
            "Diabetes": _to_01(data.get("Diabetes")),
            "Hypertension": _to_01(data.get("Hypertension")),
            "Family_History_Eye_Disease": _to_01(data.get("Family_History_Eye_Disease")),
            "Eye_Pain_Frequency": data.get("Eye_Pain_Frequency", 0),
            "Blurry_Vision_Score": data.get("Blurry_Vision_Score", 0),
            "Light_Sensitivity": _to_01(data.get("Light_Sensitivity")),
            "Eye_Strains_Per_Day": data.get("Eye_Strains_Per_Day", 0),
            "Outdoor_Exposure_Hours": data.get("Outdoor_Exposure_Hours", 0),
            "Diet_Score": data.get("Diet_Score", 5),
            "Water_Intake_Liters": data.get("Water_Intake_Liters", 0),
            "Glasses_Usage": _to_01(data.get("Glasses_Usage")),
            "Previous_Eye_Surgery": _to_01(data.get("Previous_Eye_Surgery")),
            "Physical_Activity_Level": _physical_activity_to_level(
                data.get("Physical_Activity_Level")
            ),
        }
        
        # Get ML prediction
        prediction = predict_risk(assessment_data)
        
        # Get recommendations
        recommendations = get_recommendations(
            prediction['risk_level'],
            prediction['predicted_disease'],
            assessment_data
        )
        
        # Save to database
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                assessment_id = str(uuid.uuid4())
                
                # Insert assessment result
                cur.execute("""
                    INSERT INTO assessment_results 
                    (assessment_id, user_id, risk_level, risk_score, confidence_score, 
                     predicted_disease, assessment_data, per_disease_scores, assessed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    assessment_id,
                    user_id,
                    prediction['risk_level'],
                    prediction['risk_score'],
                    prediction['confidence'] * 100,
                    prediction['predicted_disease'],
                    json.dumps(assessment_data),
                    json.dumps(prediction['per_disease_probabilities']),
                    datetime.now(timezone.utc)
                ))
                
                # Insert recommendations
                for rec in recommendations:
                    rec_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO recommendations 
                        (recommendation_id, assessment_id, recommendation_text, priority, category)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (rec_id, assessment_id, rec['text'], rec['priority'], rec['category']))
                
                # Update/insert health records, habits, and symptoms
                record_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO health_records 
                    (record_id, user_id, age, gender, bmi, diabetes, hypertension, 
                     previous_eye_surgery, date_recorded)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    record_id, user_id, assessment_data['Age'], assessment_data['Gender'],
                    assessment_data['BMI'], assessment_data['Diabetes'], 
                    assessment_data['Hypertension'], assessment_data['Previous_Eye_Surgery'],
                    datetime.now(timezone.utc).date()
                ))
                
                habit_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO habit_data 
                    (habit_id, user_id, screen_time_hours, sleep_hours, diet_quality,
                     smoking_status, alcohol_use, outdoor_activity_hours, water_intake_liters,
                     physical_activity_level, glasses_usage)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    habit_id, user_id, assessment_data['Screen_Time_Hours'],
                    assessment_data['Sleep_Hours'], assessment_data['Diet_Score'],
                    'Yes' if assessment_data['Smoker'] else 'No',
                    assessment_data['Alcohol_Use'], assessment_data['Outdoor_Exposure_Hours'],
                    assessment_data['Water_Intake_Liters'], assessment_data['Physical_Activity_Level'],
                    assessment_data['Glasses_Usage']
                ))
                
                symptom_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO eye_symptoms
                    (symptom_id, user_id, eye_pain_frequency, blurry_vision_score,
                     light_sensitivity, eye_strains_per_day, family_history_eye_disease)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    symptom_id, user_id, assessment_data['Eye_Pain_Frequency'],
                    assessment_data['Blurry_Vision_Score'],
                    'Yes' if assessment_data['Light_Sensitivity'] else 'No',
                    assessment_data['Eye_Strains_Per_Day'],
                    assessment_data['Family_History_Eye_Disease']
                ))
                
                # Commit all changes to database
                conn.commit()
        finally:
            conn.close()
        
        # Return comprehensive result
        return jsonify({
            "status": "success",
            "assessment_id": assessment_id,
            "prediction": prediction,
            "recommendations": recommendations,
            "message": "Assessment completed successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@assessment_bp.route("/api/assessment/history/<user_id>", methods=["GET"])
def get_assessment_history(user_id):
    """Get all previous assessments for a user."""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT assessment_id, risk_level, risk_score, confidence_score,
                           predicted_disease, per_disease_scores, assessment_data, assessed_at
                    FROM assessment_results
                    WHERE user_id = %s
                    ORDER BY assessed_at DESC
                    LIMIT 20
                """, (user_id,))
                assessments = cur.fetchall()
                
                # Parse per_disease_scores for each assessment
                for assessment in assessments:
                    assessment_data = _parse_json_maybe(assessment.get("assessment_data"))
                    if not isinstance(assessment_data, dict):
                        assessment_data = {}

                    if 'per_disease_scores' in assessment and assessment['per_disease_scores']:
                        try:
                            if isinstance(assessment['per_disease_scores'], str):
                                assessment['disease_probabilities'] = json.loads(assessment['per_disease_scores'])
                            else:
                                assessment['disease_probabilities'] = assessment['per_disease_scores']
                        except:
                            assessment['disease_probabilities'] = {}
                    else:
                        assessment['disease_probabilities'] = {}

                    # If legacy one-hot probabilities were stored, recompute to match confidence.
                    try:
                        predicted_disease = assessment.get("predicted_disease")
                        confidence_score = float(assessment.get("confidence_score") or 0.0)
                        if _looks_like_legacy_one_hot(
                            assessment.get("disease_probabilities") or {},
                            predicted_disease,
                        ):
                            assessment["disease_probabilities"] = _recompute_per_disease_probabilities(
                                assessment_data=assessment_data,
                                predicted_disease=str(predicted_disease),
                                confidence_score=confidence_score,
                            )
                    except Exception:
                        # Never fail the whole history endpoint due to recompute issues.
                        pass
                
                return jsonify({
                    "status": "success",
                    "assessments": assessments
                }), 200
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@assessment_bp.route("/api/assessment/detail/<assessment_id>", methods=["GET"])
def get_assessment_detail(assessment_id):
    """Get detailed information about a specific assessment."""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Get assessment
                cur.execute("""
                    SELECT * FROM assessment_results WHERE assessment_id = %s
                """, (assessment_id,))
                assessment = cur.fetchone()
                
                if not assessment:
                    return jsonify({"error": "Assessment not found"}), 404
                
                # Parse per_disease_scores if it's a JSON string
                if 'per_disease_scores' in assessment and assessment['per_disease_scores']:
                    try:
                        if isinstance(assessment['per_disease_scores'], str):
                            assessment['disease_probabilities'] = json.loads(assessment['per_disease_scores'])
                        else:
                            assessment['disease_probabilities'] = assessment['per_disease_scores']
                    except:
                        assessment['disease_probabilities'] = {}
                else:
                    assessment['disease_probabilities'] = {}

                # Recompute legacy stored one-hot probabilities to match confidence_score.
                try:
                    assessment_data = _parse_json_maybe(assessment.get("assessment_data"))
                    if not isinstance(assessment_data, dict):
                        assessment_data = {}

                    predicted_disease = assessment.get("predicted_disease")
                    confidence_score = float(assessment.get("confidence_score") or 0.0)

                    if _looks_like_legacy_one_hot(
                        assessment.get("disease_probabilities") or {},
                        predicted_disease,
                    ):
                        assessment["disease_probabilities"] = _recompute_per_disease_probabilities(
                            assessment_data=assessment_data,
                            predicted_disease=str(predicted_disease),
                            confidence_score=confidence_score,
                        )
                except Exception:
                    # Keep endpoint robust even if old records have odd shapes.
                    pass
                
                # Get recommendations
                cur.execute("""
                    SELECT recommendation_text, priority, category
                    FROM recommendations
                    WHERE assessment_id = %s
                """, (assessment_id,))
                recommendations = cur.fetchall()
                
                assessment['recommendations'] = recommendations
                return jsonify({
                    "status": "success",
                    "assessment": assessment
                }), 200
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
