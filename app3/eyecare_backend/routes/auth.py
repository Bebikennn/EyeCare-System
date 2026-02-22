# ===============================
# Authentication Routes
# ===============================
from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
from services.db import get_connection
from services.email_service import (
    generate_verification_code, 
    send_verification_email, 
    store_verification_code,
    verify_code
)
import threading
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from api_specs import AUTH_LOGIN_SPEC, AUTH_REGISTER_SPEC

auth_bp = Blueprint("auth", __name__)

# Get limiter from app context (will be set by app.py)
def get_limiter():
    from flask import current_app
    return current_app.extensions.get('limiter')

# -------------------------------
# Send Verification Code
# -------------------------------
@auth_bp.route("/send-verification-code", methods=["POST"])
def send_verification_code():
    # Apply rate limit dynamically
    limiter = get_limiter()
    if limiter:
        limiter.limit("5 per minute")(send_verification_code)
    
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    
    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400
    
    # Check if email already exists
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "Email already registered"}), 400
    finally:
        conn.close()
    
    # Generate verification code
    code = generate_verification_code()

    # Store code first so the request can return fast (important for web + Render free tier)
    store_verification_code(email, code)

    # In production, send the email asynchronously to avoid blocking the request.
    # Flask-Mail requires an application context, so we pass the app object into the thread.
    if current_app.debug:
        ok = send_verification_email(email, code)
        if not ok:
            return jsonify({"status": "error", "message": "Failed to send email. Please check your email address"}), 500
        return jsonify({"status": "success", "message": "Verification code sent to your email"}), 200

    app_obj = current_app._get_current_object()

    def _send_in_background():
        with app_obj.app_context():
            try:
                ok = send_verification_email(email, code, raise_on_error=True)
                if not ok:
                    app_obj.logger.warning("Failed to send verification email to %s", email)
            except Exception:
                app_obj.logger.exception("Error sending verification email")

    threading.Thread(target=_send_in_background, daemon=True).start()
    return jsonify({"status": "success", "message": "Verification code sent to your email"}), 200

# -------------------------------
# Verify Code
# -------------------------------
@auth_bp.route("/verify-code", methods=["POST"])
def verify_email_code():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")
    
    if not email or not code:
        return jsonify({"status": "error", "message": "Email and code are required"}), 400
    
    success, message = verify_code(email, code)
    
    if success:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 400

# -------------------------------
# User Registration
# -------------------------------
@auth_bp.route("/register", methods=["POST"])
@swag_from(AUTH_REGISTER_SPEC)
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    phone_number = data.get("phone_number")

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    # Use Werkzeug to generate secure hash (compatible with Admin Dashboard)
    password_hash = generate_password_hash(password)
    user_id = str(uuid.uuid4())

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (user_id, username, email, password_hash, full_name, phone_number)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, username, email, password_hash, full_name, phone_number))
        conn.commit()
        return jsonify({"status": "success", "message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()

# -------------------------------
# User Login
# -------------------------------
@auth_bp.route("/login", methods=["POST"])
@swag_from(AUTH_LOGIN_SPEC)
def login():
    # Rate limiting applied in app.py via limiter
    current_app.logger.info(f"Login attempt from IP: {request.remote_addr}")
    
    data = request.get_json(silent=True) or {}
    identifier = data.get("username") or data.get("email")
    password = data.get("password")

    if not identifier or not password:
        current_app.logger.warning(f"Login failed: Missing credentials from {request.remote_addr}")
        return jsonify({"status": "error", "message": "Missing username/email or password"}), 400

    conn = get_connection()
    try:
        cur = conn.cursor()
        # Fetch user first to get the stored hash
        cur.execute(
            "SELECT user_id, username, email, password_hash, status FROM users WHERE username=%s OR email=%s",
            (identifier, identifier)
        )
        user = cur.fetchone()
    finally:
        conn.close()

    # Verify password using Werkzeug
    print(f"DEBUG: Login attempt for {identifier}")
    if user:
        # Check if user is blocked
        if user.get('status') == 'blocked':
            return jsonify({"status": "error", "message": "Your account has been blocked. Please contact support."}), 403

        print(f"DEBUG: User found: {user['username']}")
        print(f"DEBUG: Stored hash: {user['password_hash']}")
        
        # Try Werkzeug check first
        is_valid = check_password_hash(user["password_hash"], password)
        print(f"DEBUG: Werkzeug check result: {is_valid}")
        
        # Fallback: Check if it's a legacy SHA256 hash (from old mobile app registrations)
        if not is_valid:
            import hashlib
            legacy_hash = hashlib.sha256(password.encode()).hexdigest()
            if legacy_hash == user["password_hash"]:
                print("DEBUG: Legacy SHA256 match found. Updating to secure hash.")
                is_valid = True
                # Optional: Update to secure hash here if you want auto-migration
                
        if is_valid:
            return jsonify({
                "status": "success", 
                "user": {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "email": user["email"]
                }
            }), 200
    else:
        print("DEBUG: User not found")

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# -------------------------------
# Forgot Password - Send Code
# -------------------------------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    
    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400
    
    # Check if email exists and get username
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username, status FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"status": "error", "message": "No account found with this email"}), 404
            
        if user.get('status') == 'blocked':
            return jsonify({"status": "error", "message": "Your account has been blocked. Please contact support."}), 403
    finally:
        conn.close()
    
    # Generate verification code
    code = generate_verification_code()

    store_verification_code(email, code)

    if current_app.debug:
        ok = send_verification_email(email, code)
        if not ok:
            return jsonify({"status": "error", "message": "Failed to send email"}), 500
        return jsonify({
            "status": "success",
            "message": "Verification code sent to your email",
            "username": user["username"]
        }), 200

    app_obj = current_app._get_current_object()

    def _send_in_background():
        with app_obj.app_context():
            try:
                ok = send_verification_email(email, code, raise_on_error=True)
                if not ok:
                    app_obj.logger.warning("Failed to send forgot-password email to %s", email)
            except Exception:
                app_obj.logger.exception("Error sending forgot-password email")

    threading.Thread(target=_send_in_background, daemon=True).start()
    return jsonify({
        "status": "success",
        "message": "Verification code sent to your email",
        "username": user["username"]
    }), 200

# -------------------------------
# Reset Password
# -------------------------------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("new_password")
    
    if not email or not new_password:
        return jsonify({"status": "error", "message": "Email and new password are required"}), 400
    
    # Hash the new password using Werkzeug
    password_hash = generate_password_hash(new_password)
    
    # Update password in database
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Check status first
        cursor.execute("SELECT status FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        if user.get('status') == 'blocked':
            return jsonify({"status": "error", "message": "Your account has been blocked. Please contact support."}), 403
            
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email)
        )
        
        conn.commit()
        return jsonify({"status": "success", "message": "Password reset successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()
