"""
Tests for authentication routes
"""
import pytest
from flask import session


class TestLogin:
    """Test login functionality"""
    
    def test_login_page_loads(self, client):
        """Test login page is accessible"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'EyeCare Admin' in response.data or b'Login' in response.data
    
    def test_login_success(self, client, admin_user):
        """Test successful login"""
        response = client.post('/api/auth/login', json={
            'username': 'testadmin',
            'password': 'TestPass123!'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Login successful'
        assert 'admin' in data
        assert data['must_change_password'] is False
    
    def test_login_invalid_username(self, client):
        """Test login with invalid username"""
        response = client.post('/api/auth/login', json={
            'username': 'nonexistent',
            'password': 'password'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_login_invalid_password(self, client, admin_user):
        """Test login with wrong password"""
        response = client.post('/api/auth/login', json={
            'username': 'testadmin',
            'password': 'WrongPassword123!'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user"""
        from database import Admin
        inactive = Admin(
            username='inactive',
            email='inactive@test.com',
            full_name='Inactive User',
            role='staff',
            status='inactive'
        )
        inactive.set_password('Pass123!')
        db_session.add(inactive)
        db_session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'inactive',
            'password': 'Pass123!'
        })
        assert response.status_code == 403
        data = response.get_json()
        assert 'inactive' in data['error'].lower()
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/api/auth/login', json={
            'username': 'testadmin'
        })
        assert response.status_code == 400
    
    def test_login_force_password_change(self, client, password_change_admin):
        """Test login redirects when password change required"""
        response = client.post('/api/auth/login', json={
            'username': 'changepass',
            'password': 'OldPass123!'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['must_change_password'] is True
        assert data['redirect'] == '/change-password'


class TestLogout:
    """Test logout functionality"""
    
    def test_logout_success(self, authenticated_client):
        """Test successful logout"""
        response = authenticated_client.post('/api/auth/logout')
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Logout successful'
    
    def test_logout_without_session(self, client):
        """Test logout without active session"""
        response = client.post('/api/auth/logout')
        assert response.status_code == 200


class TestCheckSession:
    """Test session checking"""
    
    def test_check_session_authenticated(self, authenticated_client, admin_user):
        """Test session check when authenticated"""
        response = authenticated_client.get('/api/auth/check-session')
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is True
        assert 'admin' in data
    
    def test_check_session_unauthenticated(self, client):
        """Test session check when not authenticated"""
        response = client.get('/api/auth/check-session')
        assert response.status_code == 401
        data = response.get_json()
        assert data['authenticated'] is False


class TestChangePassword:
    """Test password change functionality"""
    
    def test_change_password_success(self, authenticated_client, admin_user):
        """Test successful password change"""
        response = authenticated_client.post('/api/auth/change-password', json={
            'current_password': 'TestPass123!',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data['message'].lower()
    
    def test_change_password_wrong_current(self, authenticated_client):
        """Test password change with wrong current password"""
        response = authenticated_client.post('/api/auth/change-password', json={
            'current_password': 'WrongPass123!',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'incorrect' in data['error'].lower()
    
    def test_change_password_mismatch(self, authenticated_client):
        """Test password change with mismatched passwords"""
        response = authenticated_client.post('/api/auth/change-password', json={
            'current_password': 'TestPass123!',
            'new_password': 'NewPass456!',
            'confirm_password': 'DifferentPass789!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'match' in data['error'].lower()
    
    def test_change_password_weak(self, authenticated_client):
        """Test password change with weak password"""
        response = authenticated_client.post('/api/auth/change-password', json={
            'current_password': 'TestPass123!',
            'new_password': 'weak',
            'confirm_password': 'weak'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_change_password_not_authenticated(self, client):
        """Test password change without authentication"""
        response = client.post('/api/auth/change-password', json={
            'current_password': 'TestPass123!',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!'
        })
        assert response.status_code == 401


class TestForgotPassword:
    """Test forgot password functionality"""
    
    def test_forgot_password_valid_email(self, client, admin_user, app):
        """Test forgot password with valid email"""
        with app.app_context():
            response = client.post('/api/auth/forgot-password', json={
                'email': 'admin@test.com'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert 'message' in data
    
    def test_forgot_password_invalid_email(self, client):
        """Test forgot password with non-existent email"""
        response = client.post('/api/auth/forgot-password', json={
            'email': 'nonexistent@test.com'
        })
        # Should return 200 to prevent email enumeration
        assert response.status_code == 200
    
    def test_forgot_password_missing_email(self, client):
        """Test forgot password without email"""
        response = client.post('/api/auth/forgot-password', json={})
        assert response.status_code == 400


class TestResetPassword:
    """Test password reset functionality"""
    
    def test_reset_password_valid_token(self, client, admin_user, db_session):
        """Test password reset with valid token"""
        # Generate token
        token = admin_user.generate_reset_token()
        db_session.commit()
        
        response = client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': 'NewSecure123!',
            'confirm_password': 'NewSecure123!'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data['message'].lower()
    
    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token"""
        response = client.post('/api/auth/reset-password', json={
            'token': 'invalid_token',
            'new_password': 'NewSecure123!',
            'confirm_password': 'NewSecure123!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'invalid' in data['error'].lower() or 'expired' in data['error'].lower()
    
    def test_reset_password_mismatch(self, client, admin_user, db_session):
        """Test password reset with mismatched passwords"""
        token = admin_user.generate_reset_token()
        db_session.commit()
        
        response = client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': 'NewSecure123!',
            'confirm_password': 'Different456!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'match' in data['error'].lower()
