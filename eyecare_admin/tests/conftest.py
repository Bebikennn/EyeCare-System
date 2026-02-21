"""
Pytest configuration and fixtures for testing
"""
import pytest
import os
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Must set testing config BEFORE importing app
os.environ['TESTING'] = 'true'

from app import app as flask_app
from database import db, Admin, ActivityLog, HealthTip, User


@pytest.fixture(scope='session')
def app():
    """Create application instance for testing"""
    # Set testing configuration
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # Use in-memory SQLite for tests
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key',
        'MAIL_SUPPRESS_SEND': True,  # Don't actually send emails
        'MAIL_DEFAULT_SENDER': 'test@example.com',
        'SERVER_NAME': 'localhost.localdomain'  # Needed for url_for in tests
    })
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create CLI test runner"""
    return app.test_cli_runner()


@pytest.fixture(scope='function', autouse=True)
def db_session(app):
    """Create database session for testing - auto-cleans after each test"""
    with app.app_context():
        # Start with clean slate for each test
        yield db.session
        # Rollback any changes
        db.session.rollback()
        # Clean all tables for next test
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture(scope='function')
def admin_user(db_session):
    """Create test admin user"""
    admin = Admin(
        username='testadmin',
        email='admin@test.com',
        full_name='Test Admin',
        role='admin',
        status='active',
        must_change_password=False
    )
    admin.set_password('TestPass123!')
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture(scope='function')
def super_admin_user(db_session):
    """Create test super admin user"""
    admin = Admin(
        username='superadmin',
        email='super@test.com',
        full_name='Super Admin',
        role='super_admin',
        status='active',
        must_change_password=False
    )
    admin.set_password('SuperPass123!')
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture(scope='function')
def staff_user(db_session):
    """Create test staff user"""
    staff = Admin(
        username='teststaff',
        email='staff@test.com',
        full_name='Test Staff',
        role='staff',
        status='active',
        must_change_password=False
    )
    staff.set_password('StaffPass123!')
    db_session.add(staff)
    db_session.commit()
    return staff


@pytest.fixture(scope='function')
def password_change_admin(db_session):
    """Create admin that must change password"""
    admin = Admin(
        username='changepass',
        email='change@test.com',
        full_name='Change Pass Admin',
        role='admin',
        status='active',
        must_change_password=True
    )
    admin.set_password('OldPass123!')
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture(scope='function')
def authenticated_client(client, admin_user):
    """Create client with authenticated session"""
    with client.session_transaction() as sess:
        sess['admin_id'] = admin_user.id
        sess['admin_username'] = admin_user.username
        sess['admin_role'] = admin_user.role
    return client


@pytest.fixture(scope='function')
def health_tip(db_session):
    """Create test health tip"""
    tip = HealthTip(
        title='Test Health Tip',
        description='This is a test health tip for eye care',
        category='general',
        icon=None,
        risk_level='All',
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(tip)
    db_session.commit()
    return tip


@pytest.fixture(scope='function')
def mobile_user(db_session):
    """Create test mobile app user"""
    user = User(
        user_id='00000000-0000-0000-0000-000000000001',
        username='testuser',
        email='user@test.com',
        password_hash='hashed_password',
        full_name='Test User',
        phone_number='+1234567890',
        status='active',
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    return user
