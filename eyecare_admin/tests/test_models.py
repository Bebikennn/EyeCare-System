"""
Tests for database models
"""
import pytest
from datetime import datetime, timedelta, timezone


class TestAdminModel:
    """Test Admin model"""
    
    def test_create_admin(self, db_session):
        """Test creating an admin"""
        from database import Admin
        admin = Admin(
            username='newadmin',
            email='new@test.com',
            full_name='New Admin',
            role='staff',
            status='active'
        )
        admin.set_password('Password123!')
        db_session.add(admin)
        db_session.commit()
        
        assert admin.id is not None
        assert admin.username == 'newadmin'
        assert admin.check_password('Password123!')
    
    def test_password_hashing(self, admin_user):
        """Test password is properly hashed"""
        assert admin_user.password_hash != 'TestPass123!'
        assert len(admin_user.password_hash) > 50
    
    def test_check_password_correct(self, admin_user):
        """Test password verification with correct password"""
        assert admin_user.check_password('TestPass123!')
    
    def test_check_password_incorrect(self, admin_user):
        """Test password verification with incorrect password"""
        assert not admin_user.check_password('WrongPassword')
    
    def test_to_dict(self, admin_user):
        """Test to_dict serialization"""
        data = admin_user.to_dict()
        assert data['username'] == 'testadmin'
        assert data['email'] == 'admin@test.com'
        assert data['role'] == 'admin'
        assert 'password_hash' not in data
    
    def test_generate_reset_token(self, admin_user, db_session):
        """Test reset token generation"""
        token = admin_user.generate_reset_token()
        assert token is not None
        assert admin_user.reset_token == token
        assert admin_user.reset_token_expiry is not None
    
    def test_verify_reset_token_valid(self, admin_user, db_session):
        """Test verifying valid reset token"""
        token = admin_user.generate_reset_token()
        db_session.commit()
        assert admin_user.verify_reset_token(token)
    
    def test_verify_reset_token_invalid(self, admin_user):
        """Test verifying invalid reset token"""
        assert not admin_user.verify_reset_token('invalid_token')
    
    def test_verify_reset_token_expired(self, admin_user, db_session):
        """Test verifying expired reset token"""
        token = admin_user.generate_reset_token()
        # Set expiry to past
        admin_user.reset_token_expiry = datetime.now(timezone.utc) - timedelta(hours=2)
        db_session.commit()
        assert not admin_user.verify_reset_token(token)
    
    def test_clear_reset_token(self, admin_user, db_session):
        """Test clearing reset token"""
        admin_user.generate_reset_token()
        db_session.commit()
        admin_user.clear_reset_token()
        assert admin_user.reset_token is None
        assert admin_user.reset_token_expiry is None


class TestActivityLogModel:
    """Test ActivityLog model"""
    
    def test_create_activity_log(self, db_session, admin_user):
        """Test creating an activity log"""
        from database import ActivityLog
        log = ActivityLog(
            admin_id=admin_user.id,
            action='Test Action',
            entity_type='test',
            entity_id='123',
            details='Test details',
            ip_address='127.0.0.1'
        )
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.admin_id == admin_user.id
        assert log.action == 'Test Action'
    
    def test_activity_log_to_dict(self, db_session, admin_user):
        """Test activity log serialization"""
        from database import ActivityLog
        log = ActivityLog(
            admin_id=admin_user.id,
            action='Login',
            entity_type='auth',
            details='User logged in',
            ip_address='192.168.1.1'
        )
        db_session.add(log)
        db_session.commit()
        
        data = log.to_dict()
        assert data['action'] == 'Login'
        assert data['admin_name'] == admin_user.full_name
        assert data['ip_address'] == '192.168.1.1'


class TestHealthTipModel:
    """Test HealthTip model"""
    
    def test_create_health_tip(self, db_session):
        """Test creating a health tip"""
        from database import HealthTip
        tip = HealthTip(
            title='New Tip',
            description='Tip content',
            category='prevention',
            risk_level='All'
        )
        db_session.add(tip)
        db_session.commit()
        
        assert tip.id is not None
        assert tip.title == 'New Tip'
        assert tip.status == 'active'
    
    def test_health_tip_to_dict(self, health_tip):
        """Test health tip serialization"""
        data = health_tip.to_dict()
        assert data['title'] == 'Test Health Tip'
        assert data['category'] == 'general'
        assert 'created_at' in data


class TestUserModel:
    """Test User model (mobile app users)"""
    
    def test_create_user(self, db_session):
        """Test creating a mobile user"""
        from database import User
        user = User(
            user_id='00000000-0000-0000-0000-000000000002',
            username='mobileuser',
            email='mobile@test.com',
            password_hash='hashed',
            full_name='Mobile User',
            phone_number='+1234567890',
            status='active'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.user_id is not None
        assert user.email == 'mobile@test.com'
    
    def test_user_to_dict(self, mobile_user):
        """Test user serialization"""
        data = mobile_user.to_dict()
        assert data['email'] == 'user@test.com'
        assert data['full_name'] == 'Test User'
        assert 'password_hash' not in data
