"""
Email Service for sending verification codes
"""
from flask_mail import Mail, Message
import logging
import os
import random
import secrets
import string
from datetime import datetime, timedelta

import hashlib

import requests

from services.db import DB_DIALECT, get_connection

mail = Mail()

# In-memory fallback storage for verification codes.
# Primary storage is the database to survive multi-worker deployments and restarts.
verification_codes = {}


def _normalize_email(email: str) -> str:
    return (email or '').strip().lower()


def _normalize_code(code) -> str:
    return str(code or '').strip()


def _now_utc() -> datetime:
    return datetime.utcnow()


def _hash_code(code: str) -> str:
    pepper = (os.getenv('VERIFICATION_CODE_PEPPER') or os.getenv('SECRET_KEY') or '').strip()
    raw = f"{code}:{pepper}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _ensure_verification_table(conn) -> None:
    cur = conn.cursor()
    if DB_DIALECT == 'postgres':
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS email_verification_codes (
                email TEXT PRIMARY KEY,
                code_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    else:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS email_verification_codes (
                email VARCHAR(255) PRIMARY KEY,
                code_hash VARCHAR(64) NOT NULL,
                expires_at DATETIME NOT NULL,
                attempts INT NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


def _is_sendgrid_configured() -> bool:
    api_key = (os.getenv('SENDGRID_API_KEY') or '').strip()
    from_email = (os.getenv('SENDGRID_FROM_EMAIL') or os.getenv('MAIL_DEFAULT_SENDER') or '').strip()
    return bool(api_key and from_email)


def _send_via_sendgrid(*, to_email: str, subject: str, html: str, plain: str) -> bool:
    api_key = (os.getenv('SENDGRID_API_KEY') or '').strip()
    from_email = (os.getenv('SENDGRID_FROM_EMAIL') or os.getenv('MAIL_DEFAULT_SENDER') or '').strip()

    if not api_key or not from_email:
        return False

    payload = {
        'personalizations': [{'to': [{'email': to_email}]}],
        'from': {'email': from_email},
        'subject': subject,
        'content': [
            {'type': 'text/plain', 'value': plain},
            {'type': 'text/html', 'value': html},
        ],
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

def send_verification_email(email, code, *, raise_on_error: bool = False):
    """Send verification code to user's email.

    If raise_on_error=True, exceptions are re-raised after being logged.
    """
    try:
        provider = (os.getenv('EMAIL_PROVIDER') or 'auto').strip().lower()

        subject = "EyeCare - Email Verification Code"
        code_str = _normalize_code(code)
        plain = (
            "Welcome to EyeCare!\n\n"
            f"Your verification code is: {code_str}\n\n"
            "This code expires in 10 minutes.\n"
            "If you didn't request this, you can ignore this email.\n"
        )
        html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #1976d2;">Welcome to EyeCare!</h2>
                    <p>Thank you for registering with EyeCare. Please use the verification code below to complete your registration:</p>
                    <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; text-align: center; border-radius: 8px;">
                        <h1 style="color: #1976d2; font-size: 36px; letter-spacing: 5px; margin: 0;">{code_str}</h1>
                    </div>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;">
                    <p style="color: #666; font-size: 12px;">EyeCare - Your Eye Health Assessment App</p>
                </body>
            </html>
            """

        sendgrid_configured = _is_sendgrid_configured()

        smtp_configured = False
        try:
            from flask import current_app
            cfg = current_app.config
            smtp_configured = bool(cfg.get('MAIL_USERNAME') and cfg.get('MAIL_PASSWORD'))
        except Exception:
            # No app context available; assume SMTP may be configured.
            smtp_configured = True

        def _send_via_smtp() -> bool:
            if not smtp_configured:
                return False
            msg = Message(
                subject=subject,
                recipients=[email],
                body=(
                    "Welcome to EyeCare!\n\n"
                    f"Your verification code is: {code_str}\n\n"
                    "This code expires in 10 minutes.\n"
                    "If you didn't request this, you can ignore this email.\n"
                ),
                html=html,
            )
            mail.send(msg)
            return True

        if provider == 'sendgrid':
            if sendgrid_configured and _send_via_sendgrid(to_email=email, subject=subject, html=html, plain=plain):
                return True
            try:
                from flask import current_app
                current_app.logger.warning('EMAIL_PROVIDER=sendgrid but SendGrid is not configured or failed')
            except Exception:
                logging.getLogger(__name__).warning('EMAIL_PROVIDER=sendgrid but SendGrid is not configured or failed')
            return False

        # If the deployment is configured to use SMTP, do not attempt HTTP providers.
        if provider == 'smtp':
            if _send_via_smtp():
                return True
            try:
                from flask import current_app
                current_app.logger.warning('EMAIL_PROVIDER=smtp but SMTP is not configured')
            except Exception:
                logging.getLogger(__name__).warning('EMAIL_PROVIDER=smtp but SMTP is not configured')
            return False

        # Prefer SendGrid HTTP API when configured
        if sendgrid_configured and _send_via_sendgrid(to_email=email, subject=subject, html=html, plain=plain):
            return True

        # Only fall back to SMTP if it's actually configured.
        if smtp_configured:
            return _send_via_smtp()

        try:
            from flask import current_app
            current_app.logger.warning(
                'No email provider succeeded (SendGrid configured=%s, SMTP configured=%s)',
                sendgrid_configured,
                smtp_configured,
            )
        except Exception:
            logging.getLogger(__name__).warning(
                'No email provider succeeded (SendGrid configured=%s, SMTP configured=%s)',
                sendgrid_configured,
                smtp_configured,
            )

        return False
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
    """Store verification code with expiry time.

    Uses the database as the source of truth. Falls back to in-memory storage if DB is unavailable.
    """
    email_n = _normalize_email(email)
    code_n = _normalize_code(code)
    expiry_time = _now_utc() + timedelta(minutes=expiry_minutes)
    code_hash = _hash_code(code_n)

    conn = None
    try:
        conn = get_connection()
        _ensure_verification_table(conn)
        cur = conn.cursor()
        if DB_DIALECT == 'postgres':
            cur.execute(
                """
                INSERT INTO email_verification_codes (email, code_hash, expires_at, attempts, created_at)
                VALUES (%s, %s, %s, 0, CURRENT_TIMESTAMP)
                ON CONFLICT (email)
                DO UPDATE SET code_hash=EXCLUDED.code_hash, expires_at=EXCLUDED.expires_at, attempts=0, created_at=CURRENT_TIMESTAMP
                """,
                (email_n, code_hash, expiry_time),
            )
        else:
            cur.execute(
                """
                INSERT INTO email_verification_codes (email, code_hash, expires_at, attempts, created_at)
                VALUES (%s, %s, %s, 0, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE code_hash=VALUES(code_hash), expires_at=VALUES(expires_at), attempts=0, created_at=CURRENT_TIMESTAMP
                """,
                (email_n, code_hash, expiry_time),
            )
        conn.commit()
        return
    except Exception:
        try:
            from flask import current_app
            current_app.logger.exception('Failed to persist verification code; using in-memory fallback')
        except Exception:
            logging.getLogger(__name__).exception('Failed to persist verification code; using in-memory fallback')
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    verification_codes[email_n] = {
        'code': code_n,
        'expiry': datetime.now() + timedelta(minutes=expiry_minutes),
        'attempts': 0,
    }

def verify_code(email, code):
    """Verify if the code is valid and not expired."""
    email_n = _normalize_email(email)
    code_n = _normalize_code(code)

    # Try database first (source of truth)
    conn = None
    try:
        conn = get_connection()
        _ensure_verification_table(conn)

        # Opportunistic cleanup so the table doesn't grow unbounded
        cur = conn.cursor()
        if DB_DIALECT == 'postgres':
            cur.execute("DELETE FROM email_verification_codes WHERE expires_at < %s", (_now_utc(),))
        else:
            cur.execute("DELETE FROM email_verification_codes WHERE expires_at < %s", (_now_utc(),))
        conn.commit()

        cur.execute(
            "SELECT email, code_hash, expires_at, attempts FROM email_verification_codes WHERE email = %s",
            (email_n,),
        )
        row = cur.fetchone()

        if not row:
            return False, "No verification code found for this email"

        expires_at = row.get('expires_at')
        if getattr(expires_at, 'tzinfo', None) is not None:
            expires_at = expires_at.replace(tzinfo=None)
        attempts = int(row.get('attempts') or 0)

        # If expired, delete and reject
        if expires_at is not None and _now_utc() > expires_at:
            cur.execute("DELETE FROM email_verification_codes WHERE email = %s", (email_n,))
            conn.commit()
            return False, "Verification code has expired"

        if attempts >= 5:
            cur.execute("DELETE FROM email_verification_codes WHERE email = %s", (email_n,))
            conn.commit()
            return False, "Too many failed attempts. Please request a new code"

        expected_hash = row.get('code_hash') or ''
        provided_hash = _hash_code(code_n)

        if secrets.compare_digest(expected_hash, provided_hash):
            cur.execute("DELETE FROM email_verification_codes WHERE email = %s", (email_n,))
            conn.commit()
            return True, "Code verified successfully"

        # Wrong code: increment attempts
        cur.execute(
            "UPDATE email_verification_codes SET attempts = attempts + 1 WHERE email = %s",
            (email_n,),
        )
        conn.commit()
        return False, "Invalid verification code"
    except Exception:
        try:
            from flask import current_app
            current_app.logger.exception('DB verify_code failed; using in-memory fallback')
        except Exception:
            logging.getLogger(__name__).exception('DB verify_code failed; using in-memory fallback')
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    # Fallback: in-memory (development / DB outage)
    if email_n not in verification_codes:
        return False, "No verification code found for this email"

    stored_data = verification_codes[email_n]

    if datetime.now() > stored_data['expiry']:
        del verification_codes[email_n]
        return False, "Verification code has expired"

    if stored_data['attempts'] >= 5:
        del verification_codes[email_n]
        return False, "Too many failed attempts. Please request a new code"

    if stored_data['code'] == code_n:
        del verification_codes[email_n]
        return True, "Code verified successfully"

    stored_data['attempts'] += 1
    return False, "Invalid verification code"

def cleanup_expired_codes():
    """Remove expired verification codes"""
    now = datetime.now()
    expired_emails = [email for email, data in verification_codes.items() 
                      if now > data['expiry']]
    for email in expired_emails:
        del verification_codes[email]
