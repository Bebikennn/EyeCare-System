from flask import Blueprint, request, jsonify, session, current_app, url_for
from flask_mail import Message, Mail
from database import db, Admin, ActivityLog
from datetime import datetime, timezone
import os

import requests
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
        resp = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        if resp.status_code == 202:
            return True

        current_app.logger.error('SendGrid API error %s: %s', resp.status_code, resp.text)
        return False
    except Exception:
        current_app.logger.error('SendGrid API request failed', exc_info=True)
        return False

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
    """Send password reset email"""
    try:
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        email = data.get('email').strip().lower()
        
        # Find admin by email
        admin = Admin.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        # Don't reveal if email exists or not
        if not admin:
            return jsonify({'message': 'If an account exists with this email, a password reset link has been sent'}), 200
        
        # Check if admin is active
        if admin.status != 'active':
            return jsonify({'message': 'If an account exists with this email, a password reset link has been sent'}), 200
        
        # Generate reset token (signature-based; no DB persistence required)
        reset_token = admin.generate_reset_token()

        # Build reset link from current deployment host.
        # Prefer https in production.
        reset_link = url_for(
            'reset_password_page',
            token=reset_token,
            _external=True,
            _scheme='https' if not current_app.debug else request.scheme,
        )
        
        subject = 'Password Reset Request - EyeCare Admin'
        body = f"""
Hello {admin.full_name},

You requested to reset your password for your EyeCare Admin account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Best regards,
EyeCare Admin Team
"""
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #007bff;">Password Reset Request</h2>
    <p>Hello <strong>{admin.full_name}</strong>,</p>
    <p>You requested to reset your password for your EyeCare Admin account.</p>
    <p>Click the button below to reset your password:</p>
    <p style="margin: 30px 0;">
        <a href="{reset_link}" 
           style="background-color: #007bff; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 4px; display: inline-block;">
            Reset Password
        </a>
    </p>
    <p>Or copy and paste this link into your browser:</p>
    <p style="background: #f4f4f4; padding: 10px; border-radius: 4px; word-break: break-all;">
        {reset_link}
    </p>
    <p style="color: #dc3545; font-weight: bold;">This link will expire in 1 hour.</p>
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
        # Prefer SendGrid HTTP API on Render (avoids SMTP egress timeouts).
        email_sent = _send_reset_email_via_sendgrid(
            to_email=admin.email,
            subject=subject,
            body=body,
            html=html,
        )

        # Fallback to SMTP only when SendGrid HTTP is not configured or fails.
        if not email_sent:
            msg = Message(subject, recipients=[admin.email])
            msg.body = body
            msg.html = html

            mail_client = get_mail()
            if mail_client is not None:
                try:
                    mail_client.send(msg)
                    email_sent = True
                except Exception:
                    current_app.logger.error('Failed to send password reset email (SMTP fallback)', exc_info=True)
            else:
                current_app.logger.warning('Mail extension not initialized; cannot send reset email')

        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Password Reset Requested',
            entity_type='auth',
            details='Password reset email sent' if email_sent else 'Password reset requested (email send failed)',
            ip_address=request.remote_addr
        )
        try:
            db.session.add(log)
            db.session.commit()
        except Exception:
            # Best-effort logging only; never fail password-reset response.
            db.session.rollback()
            current_app.logger.error('Failed to write activity log for forgot-password', exc_info=True)
        
        return jsonify({'message': 'If an account exists with this email, a password reset link has been sent'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Forgot password error: {str(e)}', exc_info=True)
        # Keep generic success response to avoid account/email enumeration and UI hard failures.
        return jsonify({'message': 'If an account exists with this email, a password reset link has been sent'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        token = data.get('token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([token, new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        admin = Admin.get_by_reset_token(token)
        if not admin or not admin.verify_reset_token(token):
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        # Validate new password
        from utils.password_validator import validate_password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        admin.set_password(new_password)
        admin.clear_reset_token()
        admin.must_change_password = False
        db.session.commit()
        
        # Log activity
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