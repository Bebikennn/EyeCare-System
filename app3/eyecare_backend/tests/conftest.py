"""
EyeCare Backend Tests - Configuration
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False
    return flask_app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()
