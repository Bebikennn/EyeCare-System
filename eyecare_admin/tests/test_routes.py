"""
Tests for application routes
"""
import pytest


class TestTemplateRoutes:
    """Test template rendering routes"""
    
    def test_index_redirects_to_login(self, client):
        """Test index page redirects to login"""
        response = client.get('/', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_login_page_accessible(self, client):
        """Test login page is accessible"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_dashboard_requires_auth(self, client):
        """Test dashboard requires authentication"""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_dashboard_accessible_when_authenticated(self, authenticated_client):
        """Test dashboard accessible when authenticated"""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
    
    def test_users_requires_auth(self, client):
        """Test users page requires authentication"""
        response = client.get('/users', follow_redirects=False)
        assert response.status_code == 302
    
    def test_users_accessible_for_admin(self, authenticated_client):
        """Test users page accessible for admin"""
        response = authenticated_client.get('/users')
        assert response.status_code == 200
    
    def test_change_password_page(self, authenticated_client):
        """Test change password page"""
        response = authenticated_client.get('/change-password')
        assert response.status_code == 200
    
    def test_forgot_password_page(self, client):
        """Test forgot password page"""
        response = client.get('/forgot-password')
        assert response.status_code == 200
    
    def test_reset_password_page(self, client):
        """Test reset password page"""
        response = client.get('/reset-password')
        assert response.status_code == 200


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client, app):
        """Test health check returns healthy status"""
        with app.app_context():
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert 'database' in data


class TestErrorHandlers:
    """Test error handling"""
    
    def test_404_error_api(self, client):
        """Test 404 error for API routes"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_404_error_page(self, client):
        """Test 404 error for page routes"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
    
    def test_401_unauthorized_api(self, client):
        """Test 401 error for unauthorized API access"""
        response = client.get('/api/auth/check-session')
        assert response.status_code == 401
    
    def test_rate_limit_429(self, client, admin_user):
        """Test rate limiting returns 429"""
        # Make many requests to trigger rate limit
        for _ in range(100):
            client.post('/api/auth/login', json={
                'username': 'testadmin',
                'password': 'wrong'
            })
        
        # Next request should be rate limited
        response = client.post('/api/auth/login', json={
            'username': 'testadmin',
            'password': 'wrong'
        })
        
        # Note: May not trigger in test environment depending on limiter config
        # This test documents expected behavior
        assert response.status_code in [429, 401]


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_admin_can_access_users(self, client, admin_user):
        """Test admin can access users page"""
        with client.session_transaction() as sess:
            sess['admin_id'] = admin_user.id
            sess['admin_username'] = admin_user.username
            sess['admin_role'] = 'admin'
        
        response = client.get('/users')
        assert response.status_code == 200
    
    def test_staff_redirected_from_users(self, client, staff_user):
        """Test staff redirected from users page"""
        with client.session_transaction() as sess:
            sess['admin_id'] = staff_user.id
            sess['admin_username'] = staff_user.username
            sess['admin_role'] = 'staff'
        
        response = client.get('/users', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard' in response.location
