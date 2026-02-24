from flask import Blueprint, request, jsonify, session, current_app, url_for
from flask_mail import Message, Mail
from database import db, Admin, ActivityLog, AdminPasswordResetOTP
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
import smtplib
from email.message import EmailMessage
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

auth_bp = Blueprint('auth', __name__)

# Get limiter and mail from current_app extensions
def get_limiter():
    from flask import current_app
    return current_app.extensions.get('limiter')

def get_mail():
    from flask import current_app
    return current_app.extensions.get('mail')


def _send_reset_email_via_sendgrid(*, to_email: str, subject: str, body: str, html: str) -> bool:
    api_key = (os.getenv('SENDGRID_API_KEY') or '').strip()
    from_email = (
        os.getenv('SENDGRID_FROM_EMAIL')
        or os.getenv('MAIL_DEFAULT_SENDER')
        or ''
    ).strip()

    if not api_key or not from_email:
        return False

    payload = {
        'personalizations': [{'to': [{'email': to_email}]}],
        'from': {'email': from_email},
        'subject': subject,
        'content': [
            {'type': 'text/plain', 'value': body},
            {'type': 'text/html', 'value': html},
        ],
    }

    try:
        req = Request(
            url='https://api.sendgrid.com/v3/mail/send',
            data=json.dumps(payload).encode('utf-8'),
            method='POST',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
        )
        with urlopen(req, timeout=6) as response:
            status = getattr(response, 'status', None) or response.getcode()
        if status == 202:
            return True
        current_app.logger.error('SendGrid API error status=%s', status)
        return False
    except HTTPError as http_error:
        body_bytes = http_error.read()
        body_text = body_bytes.decode('utf-8', errors='replace') if body_bytes else ''
        current_app.logger.error('SendGrid API HTTP error %s: %s', http_error.code, body_text)
        return False
    except URLError as url_error:
        current_app.logger.error('SendGrid API URL error: %s', url_error)
        return False
    except RecursionError:
        current_app.logger.warning('SendGrid API disabled due to TLS recursion issue in runtime')
        return False
    except Exception:
        current_app.logger.error('SendGrid API request failed', exc_info=True)
        return False


def _send_reset_email_via_smtp(*, to_email: str, subject: str, body: str, html: str) -> bool:
    """Send reset email via SMTP with short timeout to avoid long UI waits."""
    server = (current_app.config.get('MAIL_SERVER') or '').strip()
    port = int(current_app.config.get('MAIL_PORT') or 25)
    use_tls = bool(current_app.config.get('MAIL_USE_TLS'))
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    sender = (
        current_app.config.get('MAIL_DEFAULT_SENDER')
        or username
        or 'no-reply@eyecare-admin.local'
    )

    timeout_seconds = int(os.getenv('ADMIN_SMTP_TIMEOUT', '6'))
    if timeout_seconds < 1:
        timeout_seconds = 1

    if not server:
        current_app.logger.warning('MAIL_SERVER is not configured; cannot send reset OTP email')
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    msg.set_content(body)
    msg.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(server, port, timeout=timeout_seconds) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except TimeoutError:
        current_app.logger.warning('SMTP timeout while sending reset OTP email (timeout=%ss)', timeout_seconds)
        return False
    except Exception:
        current_app.logger.error('Failed to send password reset OTP email (SMTP)', exc_info=True)
        return False


def _ensure_admin_otp_table() -> None:
    """Ensure OTP table exists before use (safe/idempotent)."""
    AdminPasswordResetOTP.__table__.create(bind=db.engine, checkfirst=True)


def _generate_otp_code() -> str:
    """Generate a zero-padded 6-digit OTP."""
    return f'{secrets.randbelow(1000000):06d}'

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with rate limiting (CSRF exempt at app level)"""
    
    # Apply rate limiting manually if needed
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        admin = Admin.query.filter_by(username=username).first()
        
        if not admin or not admin.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if admin.status != 'active':
            return jsonify({'error': 'Account is inactive'}), 403
        
        # Update last login
        admin.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        # Set session with permanent flag for 2-hour timeout
        session.permanent = True
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username
        session['admin_role'] = admin.role
        
        # Check if password change is required
        if admin.must_change_password:
            session['must_change_password'] = True
            
            # Log activity
            log = ActivityLog(
                admin_id=admin.id,
                action='Login - Password Change Required',
                entity_type='auth',
                details=f'Admin {admin.username} logged in - must change password',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            
            return jsonify({
                'message': 'Login successful',
                'must_change_password': True,
                'redirect': '/change-password',
                'admin': admin.to_dict()
            }), 200
        
        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Login',
            entity_type='auth',
            details=f'Admin {admin.username} logged in',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'must_change_password': False,
            'admin': admin.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        admin_id = session.get('admin_id')
        
        if admin_id:
            # Log activity
            log = ActivityLog(
                admin_id=admin_id,
                action='Logout',
                entity_type='auth',
                details='Admin logged out',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        
        session.clear()
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    if 'admin_id' in session:
        admin = Admin.query.get(session['admin_id'])
        if admin:
            response = {
                'authenticated': True,
                'admin': admin.to_dict()
            }
            # Check if password change is required
            if session.get('must_change_password'):
                response['must_change_password'] = True
            return jsonify(response), 200
    
    return jsonify({'authenticated': False}), 401

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change password endpoint - for forced password changes and user-initiated changes"""
    try:
        # Check if user is authenticated
        if 'admin_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        # Get admin
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Verify current password
        if not admin.check_password(current_password):
            # Log failed attempt
            log = ActivityLog(
                admin_id=admin.id,
                action='Password Change Failed',
                entity_type='auth',
                details='Incorrect current password',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Import password validator
        from utils.password_validator import validate_password
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        admin.set_password(new_password)
        admin.must_change_password = False
        db.session.commit()
        
        # Clear the must_change_password flag from session
        session.pop('must_change_password', None)
        
        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Password Changed',
            entity_type='auth',
            details='Admin successfully changed password',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully',
            'must_change_password': False
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send OTP email for password reset."""
    try:
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        email = data.get('email').strip().lower()
        generic_message = 'If an account exists with this email, a password reset OTP has been sent'
        
        # Find admin by email
        admin = Admin.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        # Don't reveal if email exists or not
        if not admin:
            return jsonify({'message': generic_message}), 200
        
        # Check if admin is active
        if admin.status != 'active':
            return jsonify({'message': generic_message}), 200

        _ensure_admin_otp_table()

        otp_code = _generate_otp_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Replace any prior active OTPs for this admin.
        AdminPasswordResetOTP.query.filter_by(admin_id=admin.id, consumed=False).delete(synchronize_session=False)

        otp_record = AdminPasswordResetOTP(
            admin_id=admin.id,
            otp_hash=generate_password_hash(otp_code),
            expires_at=expires_at,
            attempts=0,
            consumed=False,
        )
        db.session.add(otp_record)
        db.session.commit()
        
        subject = 'Your EyeCare Admin Password Reset OTP'
        body = f"""
Hello {admin.full_name},

You requested to reset your EyeCare Admin password.

Your one-time password (OTP) is:
{otp_code}

This OTP expires in 10 minutes and can only be used once.

If you did not request a password reset, please ignore this email.

Best regards,
EyeCare Admin Team
"""
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #007bff;">Password Reset OTP</h2>
    <p>Hello <strong>{admin.full_name}</strong>,</p>
    <p>You requested to reset your EyeCare Admin password.</p>
    <p>Use this OTP code to continue:</p>
    <p style="margin: 20px 0;">
        <span style="display: inline-block; font-size: 28px; letter-spacing: 6px; font-weight: bold; background: #f4f4f4; padding: 12px 16px; border-radius: 6px;">
            {otp_code}
        </span>
    </p>
    <p style="color: #dc3545; font-weight: bold;">This OTP expires in 10 minutes.</p>
    <p>If you did not request a password reset, please ignore this email.</p>
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    <p style="color: #666; font-size: 12px;">
        Best regards,<br>
        EyeCare Admin Team
    </p>
</body>
</html>
"""

        email_sent = False
        provider = (os.getenv('ADMIN_EMAIL_PROVIDER') or 'auto').strip().lower()

        # Prefer SendGrid API in auto mode when available (more reliable on Render).
        if provider in ('sendgrid', 'sendgrid_api', 'auto'):
            email_sent = _send_reset_email_via_sendgrid(
                to_email=admin.email,
                subject=subject,
                body=body,
                html=html,
            )

        # SMTP fallback with short timeout.
        if not email_sent and provider in ('smtp', 'sendgrid', 'sendgrid_api', 'auto'):
            email_sent = _send_reset_email_via_smtp(
                to_email=admin.email,
                subject=subject,
                body=body,
                html=html,
            )

        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Password Reset OTP Requested',
            entity_type='auth',
            details='Password reset OTP email sent' if email_sent else 'Password reset OTP requested (email send failed)',
            ip_address=request.remote_addr
        )
        try:
            db.session.add(log)
            db.session.commit()
        except Exception:
            # Best-effort logging only; never fail password-reset response.
            db.session.rollback()
            current_app.logger.error('Failed to write activity log for forgot-password OTP', exc_info=True)

        return jsonify({'message': generic_message}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Forgot password error: {str(e)}', exc_info=True)
        # Keep generic success response to avoid account/email enumeration and UI hard failures.
        return jsonify({'message': 'If an account exists with this email, a password reset OTP has been sent'}), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with OTP (or legacy token)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        token = (data.get('token') or '').strip()
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not all([new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400

        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        # Validate new password
        from utils.password_validator import validate_password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400

        if token:
            admin = Admin.get_by_reset_token(token)
            if not admin or not admin.verify_reset_token(token):
                return jsonify({'error': 'Invalid or expired reset token'}), 400

            admin.set_password(new_password)
            admin.clear_reset_token()
            admin.must_change_password = False
            db.session.commit()

            log = ActivityLog(
                admin_id=admin.id,
                action='Password Reset Completed',
                entity_type='auth',
                details='Password successfully reset via email token',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({'message': 'Password has been reset successfully. You can now login with your new password.'}), 200

        email = (data.get('email') or '').strip().lower()
        otp = (data.get('otp') or '').strip()

        if not email or not otp:
            return jsonify({'error': 'Email and OTP are required'}), 400

        admin = Admin.query.filter_by(email=email, status='active').first()
        if not admin:
            return jsonify({'error': 'Invalid or expired OTP'}), 400

        _ensure_admin_otp_table()

        now = datetime.now(timezone.utc)
        otp_record = (
            AdminPasswordResetOTP.query
            .filter(
                AdminPasswordResetOTP.admin_id == admin.id,
                AdminPasswordResetOTP.consumed.is_(False),
                AdminPasswordResetOTP.expires_at > now,
            )
            .order_by(AdminPasswordResetOTP.created_at.desc())
            .first()
        )

        if not otp_record:
            return jsonify({'error': 'Invalid or expired OTP'}), 400

        if otp_record.attempts >= 5:
            return jsonify({'error': 'Too many invalid attempts. Please request a new OTP.'}), 429

        if not check_password_hash(otp_record.otp_hash, otp):
            otp_record.attempts = (otp_record.attempts or 0) + 1
            db.session.commit()
            return jsonify({'error': 'Invalid or expired OTP'}), 400

        admin.set_password(new_password)
        admin.must_change_password = False

        otp_record.consumed = True
        otp_record.consumed_at = now

        log = ActivityLog(
            admin_id=admin.id,
            action='Password Reset Completed',
            entity_type='auth',
            details='Password successfully reset via OTP',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'message': 'Password has been reset successfully. You can now login with your new password.'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Reset password error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Failed to reset password. Please try again.'}), 500


@auth_bp.route('/send-verification-email', methods=['POST'])
def send_verification_email():
    """Send email verification link to authenticated admin"""
    # Apply rate limiting
    limiter = get_limiter()
    if limiter:
        limiter.limit("5 per hour")
    
    if 'admin_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        admin_id = session['admin_id']
        admin = db.session.query(Admin).filter_by(id=admin_id).first()
        
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
            
        if admin.email_verified:
            return jsonify({'message': 'Email already verified'}), 200
        
        # Generate verification token
        token = admin.generate_email_verification_token()
        db.session.commit()
        
        # Create verification link
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        
        # Send email
        msg = Message(
            'Verify Your Email Address',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[admin.email]
        )
        msg.body = f'''Hello {admin.username},

Please click the link below to verify your email address:

{verification_url}

This link will expire in 24 hours.

If you did not request this, please ignore this email.

Best regards,
EyeCare Admin Team
'''
        msg.html = f'''
        <html>
        <body>
            <h2>Verify Your Email Address</h2>
            <p>Hello {admin.username},</p>
            <p>Please click the button below to verify your email address:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not request this, please ignore this email.</p>
            <p>Best regards,<br>EyeCare Admin Team</p>
        </body>
        </html>
        '''
        
        get_mail().send(msg)
        
        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Verification Email Sent',
            entity_type='auth',
            details=f'Email verification sent to {admin.email}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Verification email sent successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Send verification email error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Failed to send verification email. Please try again.'}), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email address with token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        # Verify token
        admin = Admin.verify_email_token(token)
        
        if not admin:
            return jsonify({'error': 'Invalid or expired verification token'}), 400
        
        if admin.email_verified:
            return jsonify({'message': 'Email already verified'}), 200
        
        # Mark email as verified
        admin.mark_email_verified()
        
        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Email Verified',
            entity_type='auth',
            details=f'Email {admin.email} successfully verified',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Email verified successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Verify email error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Failed to verify email. Please try again.'}), 500