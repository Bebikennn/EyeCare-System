"""
Email Service for sending verification codes
"""
from flask_mail import Mail, Message
import logging
import random
import string
from datetime import datetime, timedelta

mail = Mail()

# In-memory storage for verification codes (use Redis in production)
verification_codes = {}

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Send verification code to user's email"""
    try:
        # Fail fast if SMTP isn't configured
        try:
            from flask import current_app
            cfg = current_app.config
            if not cfg.get('MAIL_USERNAME') or not cfg.get('MAIL_PASSWORD'):
                current_app.logger.warning('SMTP not configured; cannot send verification email')
                return False
        except Exception:
            # No app context available; continue and let Flask-Mail raise if misconfigured.
            pass

        msg = Message(
            subject="EyeCare - Email Verification Code",
            recipients=[email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #1976d2;">Welcome to EyeCare!</h2>
                    <p>Thank you for registering with EyeCare. Please use the verification code below to complete your registration:</p>
                    <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; text-align: center; border-radius: 8px;">
                        <h1 style="color: #1976d2; font-size: 36px; letter-spacing: 5px; margin: 0;">{code}</h1>
                    </div>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;">
                    <p style="color: #666; font-size: 12px;">EyeCare - Your Eye Health Assessment App</p>
                </body>
            </html>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        # Use Flask logger when possible so the full traceback appears in Render logs
        try:
            from flask import current_app
            current_app.logger.exception('Error sending verification email')
        except Exception:
            logging.getLogger(__name__).exception('Error sending verification email')
        return False

def store_verification_code(email, code, expiry_minutes=10):
    """Store verification code with expiry time"""
    expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
    verification_codes[email] = {
        'code': code,
        'expiry': expiry_time,
        'attempts': 0
    }

def verify_code(email, code):
    """Verify if the code is valid and not expired"""
    if email not in verification_codes:
        return False, "No verification code found for this email"
    
    stored_data = verification_codes[email]
    
    # Check if code has expired
    if datetime.now() > stored_data['expiry']:
        del verification_codes[email]
        return False, "Verification code has expired"
    
    # Check if too many attempts
    if stored_data['attempts'] >= 5:
        del verification_codes[email]
        return False, "Too many failed attempts. Please request a new code"
    
    # Verify code
    if stored_data['code'] == code:
        del verification_codes[email]
        return True, "Code verified successfully"
    else:
        stored_data['attempts'] += 1
        return False, "Invalid verification code"

def cleanup_expired_codes():
    """Remove expired verification codes"""
    now = datetime.now()
    expired_emails = [email for email, data in verification_codes.items() 
                      if now > data['expiry']]
    for email in expired_emails:
        del verification_codes[email]
