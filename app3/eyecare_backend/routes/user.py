# ===============================
# User Routes
# ===============================
from flask import Blueprint, request, jsonify
from services.db import get_connection
from datetime import datetime, timezone
import os
from werkzeug.utils import secure_filename
import uuid

user_bp = Blueprint("user", __name__)

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'profile_pictures')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@user_bp.route("/api/user/profile", methods=["GET"])
def get_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, full_name, email, phone_number AS phone, address, profile_picture_url, created_at, updated_at "
                "FROM users WHERE user_id=%s",
                (user_id,),
            )
            user = cur.fetchone()
            if not user:
                return jsonify({"error": "user not found"}), 404

            # latest health record
            cur.execute(
                "SELECT age, gender, bmi, medical_history, blood_pressure, blood_sugar, date_recorded "
                "FROM health_records WHERE user_id=%s ORDER BY date_recorded DESC LIMIT 1",
                (user_id,),
            )
            health = cur.fetchone() or {}

            # latest habits
            cur.execute(
                "SELECT screen_time_hours, sleep_hours, diet_quality, smoking_status, "
                "outdoor_activity_hours, water_intake_liters, physical_activity_level, "
                "glasses_usage, recorded_at "
                "FROM habit_data WHERE user_id=%s ORDER BY recorded_at DESC LIMIT 1",
                (user_id,),
            )
            habit = cur.fetchone() or {}

            # latest assessment result
            cur.execute(
                "SELECT risk_level AS risk_category, confidence_score AS latest_risk_score, predicted_disease, assessed_at "
                "FROM assessment_results WHERE user_id=%s ORDER BY assessed_at DESC LIMIT 1",
                (user_id,),
            )
            assessment = cur.fetchone() or {}

        # normalize numeric fields
        if assessment.get("latest_risk_score") is not None:
            try:
                assessment["latest_risk_score"] = float(assessment["latest_risk_score"])
            except Exception:
                assessment["latest_risk_score"] = 0.0

        return jsonify({"user": user, "health": health, "habit": habit, "assessment": assessment}), 200
    finally:
        conn.close()


@user_bp.route("/api/user/update", methods=["POST"])
def update_profile():
    payload = request.get_json(force=True, silent=True)
    if not payload or "user_id" not in payload:
        return jsonify({"error": "user_id required"}), 400

    user_id = payload["user_id"]
    fullname = payload.get("full_name")
    phone = payload.get("phone_number")
    email = payload.get("email")
    address = payload.get("address")
    age = payload.get("age")
    gender = payload.get("gender")
    
    # Habit data fields
    sleep_hours = payload.get("sleep_hours")
    screen_time = payload.get("screen_time")
    water_intake = payload.get("water_intake")
    activity_level = payload.get("activity_level")
    diet_quality = payload.get("diet_quality")
    smoker = payload.get("smoker")
    family_history = payload.get("family_history")
    uses_sunglasses = payload.get("uses_sunglasses")

    now = datetime.now(timezone.utc)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # update users table (full_name, email, phone_number, address)
            update_fields = []
            params = []
            if fullname is not None:
                update_fields.append("full_name=%s")
                params.append(fullname)
            if email is not None:
                update_fields.append("email=%s")
                params.append(email)
            if phone is not None:
                update_fields.append("phone_number=%s")
                params.append(phone)
            if address is not None:
                update_fields.append("address=%s")
                params.append(address)

            if update_fields:
                params.append(user_id)
                cur.execute(
                    f"UPDATE users SET {', '.join(update_fields)}, updated_at=%s WHERE user_id=%s",
                    tuple(params[:-1] + [now, params[-1]]),
                )

            # Insert or update health_records
            if age is not None or gender is not None:
                record_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO health_records (record_id, user_id, age, gender, date_recorded) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (record_id, user_id, age, gender, now.date()),
                )

            # Insert or update habit_data with all fields
            if any([sleep_hours, screen_time, water_intake, activity_level, diet_quality, smoker, uses_sunglasses]):
                # Convert boolean to smoking_status
                smoking_status = 'Yes' if smoker else 'No'
                
                # Map diet_quality if needed
                diet_val = diet_quality if isinstance(diet_quality, int) else 5
                
                habit_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO habit_data (habit_id, user_id, sleep_hours, screen_time_hours, "
                    "water_intake_liters, physical_activity_level, diet_quality, smoking_status, "
                    "glasses_usage, recorded_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        habit_id,
                        user_id,
                        sleep_hours,
                        screen_time,
                        water_intake if water_intake else 2.0,
                        activity_level,
                        diet_val,
                        smoking_status,
                        1 if uses_sunglasses else 0,
                        now,
                    ),
                )

        conn.commit()
        
        # Return updated aggregated profile
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, full_name, email, phone_number AS phone, created_at, updated_at "
                "FROM users WHERE user_id=%s",
                (user_id,),
            )
            user = cur.fetchone() or {}

            cur.execute(
                "SELECT age, gender, bmi, medical_history, blood_pressure, blood_sugar, date_recorded "
                "FROM health_records WHERE user_id=%s ORDER BY date_recorded DESC LIMIT 1",
                (user_id,),
            )
            health = cur.fetchone() or {}

            cur.execute(
                "SELECT screen_time_hours, sleep_hours, diet_quality, smoking_status, "
                "outdoor_activity_hours, water_intake_liters, physical_activity_level, "
                "glasses_usage, recorded_at "
                "FROM habit_data WHERE user_id=%s ORDER BY recorded_at DESC LIMIT 1",
                (user_id,),
            )
            habit = cur.fetchone() or {}

            cur.execute(
                "SELECT risk_level AS risk_category, confidence_score AS latest_risk_score, "
                "predicted_disease, assessed_at "
                "FROM assessment_results WHERE user_id=%s ORDER BY assessed_at DESC LIMIT 1",
                (user_id,),
            )
            assessment = cur.fetchone() or {}

        if assessment.get("latest_risk_score") is not None:
            try:
                assessment["latest_risk_score"] = float(assessment["latest_risk_score"])
            except Exception:
                assessment["latest_risk_score"] = 0.0

        return jsonify({"status": "success", "user": user, "health": health, "habit": habit, "assessment": assessment}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()

@user_bp.route("/api/user/upload-profile-picture", methods=["POST"])
def upload_profile_picture():
    """Upload profile picture for user"""
    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "error": "user_id required"}), 400

    # Check if file is in request
    if 'profile_picture' not in request.files:
        return jsonify({"status": "error", "error": "No file provided"}), 400

    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({"status": "error", "error": "No file selected"}), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return jsonify({"status": "error", "error": "File too large. Max 5MB"}), 400

    # Validate file type
    if not allowed_file(file.filename):
        return jsonify({"status": "error", "error": "Invalid file type. Allowed: png, jpg, jpeg, gif"}), 400

    try:
        # Save the file
        filename = secure_filename(f"profile_{user_id}_{datetime.now().timestamp()}.jpg")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Store file path in database with full URL for network access
        from flask import request as flask_request
        base_url = f"{flask_request.scheme}://{flask_request.host}"
        profile_picture_url = f"{base_url}/static/uploads/profile_pictures/{filename}"
        
        conn = get_connection()
        with conn.cursor() as cur:
            # Update users table with profile picture URL
            cur.execute(
                "UPDATE users SET profile_picture_url=%s, updated_at=%s WHERE user_id=%s",
                (profile_picture_url, datetime.now(), user_id)
            )
            conn.commit()

        return jsonify({
            "status": "success",
            "message": "Profile picture uploaded successfully",
            "profile_picture_url": profile_picture_url
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "error": f"Upload failed: {str(e)}"}), 500
    finally:
        conn.close()