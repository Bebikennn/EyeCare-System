"""
Tests for utility functions
"""
import pytest


class TestPasswordValidator:
    """Test password validation utilities"""
    
    def test_valid_password(self):
        """Test validation of valid password"""
        from utils.password_validator import validate_password
        is_valid, message = validate_password('SecurePass123!')
        assert is_valid is True
        assert message == 'Password is valid'
    
    def test_password_too_short(self):
        """Test password that's too short"""
        from utils.password_validator import validate_password
        is_valid, message = validate_password('Short1!')
        assert is_valid is False
        assert 'at least 8 characters' in message
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letter"""
        from utils.password_validator import validate_password
        is_valid, message = validate_password('password123!')
        assert is_valid is False
        assert 'uppercase' in message.lower()
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letter"""
        from utils.password_validator import validate_password
        is_valid, message = validate_password('PASSWORD123!')
        assert is_valid is False
        assert 'lowercase' in message.lower()
    
    def test_password_no_number(self):
        """Test password without number"""
        from utils.password_validator import validate_password
        is_valid, message = validate_password('PasswordOnly!')
        assert is_valid is False
        assert 'number' in message.lower()
    
    def test_password_no_special(self):
        """Test password without special character"""
        from utils.password_validator import validate_password
        is_valid, message = validate_password('Password123')
        assert is_valid is False
        assert 'special character' in message.lower()
    
    def test_check_password_strength_weak(self):
        """Test weak password strength"""
        from utils.password_validator import check_password_strength
        strength = check_password_strength('pass')
        assert strength == 'weak'
    
    def test_check_password_strength_medium(self):
        """Test medium password strength"""
        from utils.password_validator import check_password_strength
        strength = check_password_strength('Password1')
        assert strength == 'medium'
    
    def test_check_password_strength_strong(self):
        """Test strong password strength"""
        from utils.password_validator import check_password_strength
        strength = check_password_strength('SecureP@ssw0rd123!')
        assert strength == 'strong'
