"""
Email Service for sending verification codes
"""
from flask_mail import Mail, Message
import logging
import os
import random
import string
from datetime import datetime, timedelta

import requests

mail = Mail()

# In-memory storage for verification codes (use Redis in production)
verification_codes = {}

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


def _send_via_sendgrid(*, to_email: str, subject: str, html: str) -> bool:
    api_key = (os.getenv('SENDGRID_API_KEY') or '').strip()
    from_email = (os.getenv('SENDGRID_FROM_EMAIL') or os.getenv('MAIL_DEFAULT_SENDER') or '').strip()

    if not api_key or not from_email:
        return False

    payload = {
        'personalizations': [{'to': [{'email': to_email}]}],
        'from': {'email': from_email},
        'subject': subject,
        'content': [{'type': 'text/html', 'value': html}],
    }

    try:
        resp = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        # SendGrid returns 202 Accepted on success
        if resp.status_code == 202:
            return True

        try:
            body = resp.text
        except Exception:
            body = '<unreadable response body>'

        try:
            from flask import current_app
            current_app.logger.error('SendGrid error %s: %s', resp.status_code, body)
        except Exception:
            logging.getLogger(__name__).error('SendGrid error %s: %s', resp.status_code, body)

        return False
    except Exception:
        try:
            from flask import current_app
            current_app.logger.exception('SendGrid request failed')
        except Exception:
            logging.getLogger(__name__).exception('SendGrid request failed')
        return False


def _send_via_mailjet(*, to_email: str, subject: str, html: str) -> bool:
    # Support both variable names to reduce deploy friction.
    api_key = (os.getenv('MAILJET_API_KEY') or os.getenv('MAILJET_API') or '').strip()
    api_secret = (os.getenv('MAILJET_API_SECRET') or '').strip()
    from_email = (os.getenv('MAILJET_FROM_EMAIL') or os.getenv('MAIL_DEFAULT_SENDER') or '').strip()
    from_name = (os.getenv('MAILJET_FROM_NAME') or 'EyeCare').strip()

    if not api_key or not api_secret or not from_email:
        return False

    payload = {
        'Messages': [
            {
                'From': {'Email': from_email, 'Name': from_name},
                'To': [{'Email': to_email}],
                'Subject': subject,
                'HTMLPart': html,
            }
        ]
    }

    try:
        resp = requests.post(
            'https://api.mailjet.com/v3.1/send',
            auth=(api_key, api_secret),
            json=payload,
            timeout=15,
        )

        if 200 <= resp.status_code < 300:
            return True

        try:
            body = resp.text
        except Exception:
            body = '<unreadable response body>'

        try:
            from flask import current_app
            current_app.logger.error('Mailjet error %s: %s', resp.status_code, body)
        except Exception:
            logging.getLogger(__name__).error('Mailjet error %s: %s', resp.status_code, body)

        return False
    except Exception:
        try:
            from flask import current_app
            current_app.logger.exception('Mailjet request failed')
        except Exception:
            logging.getLogger(__name__).exception('Mailjet request failed')
        return False

def send_verification_email(email, code, *, raise_on_error: bool = False):
    """Send verification code to user's email.

    If raise_on_error=True, exceptions are re-raised after being logged.
    """
    try:
        subject = "EyeCare - Email Verification Code"
        html = f"""
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

        # Prefer Mailjet HTTP API when configured (Render often blocks outbound SMTP)
        if _send_via_mailjet(to_email=email, subject=subject, html=html):
            return True

        # Prefer SendGrid HTTP API when configured
        if _send_via_sendgrid(to_email=email, subject=subject, html=html):
            return True

        # Fallback to SMTP via Flask-Mail (useful for local dev)
        try:
            from flask import current_app
            cfg = current_app.config
            if not cfg.get('MAIL_USERNAME') or not cfg.get('MAIL_PASSWORD'):
                current_app.logger.warning('SMTP not configured; cannot send verification email')
                return False
        except Exception:
            # No app context available; continue and let Flask-Mail raise if misconfigured.
            pass
        msg = Message(subject=subject, recipients=[email], html=html)
        mail.send(msg)
        return True
    except Exception as e:
        # Use Flask logger when possible so the full traceback appears in Render logs
        try:
            from flask import current_app
            current_app.logger.exception('Error sending verification email')
        except Exception:
            logging.getLogger(__name__).exception('Error sending verification email')
        if raise_on_error:
            raise
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
