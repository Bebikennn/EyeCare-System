"""
Validation schemas for EyeCare Admin
"""
from marshmallow import Schema, fields, validate, ValidationError

class UserCreateSchema(Schema):
    """Schema for creating a new user"""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'Username is required'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required', 'invalid': 'Invalid email format'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        error_messages={'required': 'Password is required'}
    )
    full_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'Full name is required'}
    )
    phone_number = fields.Str(
        allow_none=True,
        validate=validate.Regexp(r'^\+?[\d\s\-()]+$', error='Invalid phone number format')
    )

class UserUpdateSchema(Schema):
    """Schema for updating a user"""
    username = fields.Str(validate=validate.Length(min=3, max=50))
    email = fields.Email()
    full_name = fields.Str(validate=validate.Length(min=2, max=100))
    phone_number = fields.Str(
        allow_none=True,
        validate=validate.Regexp(r'^\+?[\d\s\-()]+$', error='Invalid phone number format')
    )
    status = fields.Str(validate=validate.OneOf(['active', 'blocked', 'archived']))

class AdminCreateSchema(Schema):
    """Schema for creating a new admin"""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'Username is required'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required', 'invalid': 'Invalid email format'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        error_messages={'required': 'Password is required'}
    )
    role = fields.Str(
        required=True,
        validate=validate.OneOf(['super_admin', 'admin', 'data_analyst', 'staff']),
        error_messages={'required': 'Role is required'}
    )

class AdminUpdateSchema(Schema):
    """Schema for updating an admin"""
    username = fields.Str(validate=validate.Length(min=3, max=50))
    email = fields.Email()
    role = fields.Str(validate=validate.OneOf(['super_admin', 'admin', 'data_analyst', 'staff']))
    status = fields.Str(validate=validate.OneOf(['active', 'inactive']))

class HealthTipCreateSchema(Schema):
    """Schema for creating a health tip"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=200),
        error_messages={'required': 'Title is required'}
    )
    description = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=1000),
        error_messages={'required': 'Description is required'}
    )
    category = fields.Str(
        required=True,
        validate=validate.OneOf(['Prevention', 'Nutrition', 'Exercise', 'Eye Care']),
        error_messages={'required': 'Category is required'}
    )
    status = fields.Str(validate=validate.OneOf(['active', 'inactive']))
    image_url = fields.Str(allow_none=True)

class HealthTipUpdateSchema(Schema):
    """Schema for updating a health tip"""
    title = fields.Str(validate=validate.Length(min=5, max=200))
    description = fields.Str(validate=validate.Length(min=10, max=1000))
    category = fields.Str(validate=validate.OneOf(['Prevention', 'Nutrition', 'Exercise', 'Eye Care']))
    status = fields.Str(validate=validate.OneOf(['active', 'inactive']))
    image_url = fields.Str(allow_none=True)

class AssessmentCreateSchema(Schema):
    """Schema for creating an assessment"""
    user_id = fields.Str(required=True, error_messages={'required': 'User ID is required'})
    risk_level = fields.Str(
        required=True,
        validate=validate.OneOf(['Low', 'Moderate', 'High']),
        error_messages={'required': 'Risk level is required'}
    )
    predicted_disease = fields.Str(allow_none=True)
    risk_score = fields.Float(validate=validate.Range(min=0, max=100))
    confidence = fields.Float(validate=validate.Range(min=0, max=1))

class PasswordChangeSchema(Schema):
    """Schema for password change"""
    current_password = fields.Str(
        required=True,
        error_messages={'required': 'Current password is required'}
    )
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        error_messages={'required': 'New password is required'}
    )
    confirm_password = fields.Str(
        required=True,
        error_messages={'required': 'Confirm password is required'}
    )

class ApprovalSubmitSchema(Schema):
    """Schema for submitting an approval request"""
    action_type = fields.Str(
        required=True,
        error_messages={'required': 'Action type is required'}
    )
    target_id = fields.Str(allow_none=True)
    data = fields.Dict(allow_none=True)
    reason = fields.Str(validate=validate.Length(max=500))
