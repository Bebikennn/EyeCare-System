"""
Password validation utilities
"""
import re

def validate_password(password):
    """
    Validate password strength according to security policy.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter (A-Z)
    - Contains lowercase letter (a-z)
    - Contains number (0-9)
    - Contains special character (!@#$%^&*(),.?":{}|<>)
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number (0-9)"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Password is valid"

def check_password_strength(password):
    """
    Check password strength and return a rating.
    
    Returns:
        str: 'weak', 'medium', or 'strong'
    """
    if not password:
        return "weak"
    
    score = 0
    
    # Length checks
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # Character type checks
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    
    if score < 3:
        return "weak"
    elif score < 5:
        return "medium"
    else:
        return "strong"
