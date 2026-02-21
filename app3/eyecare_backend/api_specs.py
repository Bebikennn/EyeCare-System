"""
API Documentation endpoints with Swagger/Flasgger annotations
This file adds comprehensive API documentation to key routes
"""

from flask import Blueprint
from flasgger import swag_from

# Create example documented endpoints that can be imported
documented_routes = Blueprint('docs', __name__)

# Example swagger specs for each major endpoint

AUTH_LOGIN_SPEC = {
    "tags": ["Authentication"],
    "summary": "User login",
    "description": "Authenticate a user with username/email and password",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {
                        "type": "string",
                        "example": "john_doe",
                        "description": "Username or email"
                    },
                    "password": {
                        "type": "string",
                        "example": "SecurePass123!",
                        "description": "User password"
                    }
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Login successful",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "message": {"type": "string", "example": "Login successful"},
                    "user_id": {"type": "string", "example": "user_123"},
                    "username": {"type": "string", "example": "john_doe"},
                    "token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
                }
            }
        },
        "401": {
            "description": "Invalid credentials"
        },
        "400": {
            "description": "Missing required fields"
        }
    }
}

AUTH_REGISTER_SPEC = {
    "tags": ["Authentication"],
    "summary": "Register new user",
    "description": "Create a new user account",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["username", "email", "password", "full_name"],
                "properties": {
                    "username": {"type": "string", "example": "john_doe"},
                    "email": {"type": "string", "example": "john@example.com"},
                    "password": {"type": "string", "example": "SecurePass123!"},
                    "full_name": {"type": "string", "example": "John Doe"}
                }
            }
        }
    ],
    "responses": {
        "201": {"description": "User registered successfully"},
        "400": {"description": "Validation error or user already exists"}
    }
}

ASSESSMENT_SUBMIT_SPEC = {
    "tags": ["Assessment"],
    "summary": "Submit health assessment",
    "description": "Submit user health data for AI-powered eye disease risk assessment",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["user_id", "age", "screen_time_hours", "sleep_hours", "diet_quality"],
                "properties": {
                    "user_id": {"type": "string", "example": "user_123"},
                    "age": {"type": "integer", "example": 30},
                    "gender": {"type": "string", "example": "Male"},
                    "bmi": {"type": "number", "example": 24.5},
                    "screen_time_hours": {"type": "number", "example": 8},
                    "sleep_hours": {"type": "number", "example": 7},
                    "diet_quality": {"type": "integer", "example": 3},
                    "smoking_status": {"type": "string", "example": "Non-smoker"},
                    "outdoor_activity_hours": {"type": "number", "example": 2},
                    "water_intake_liters": {"type": "number", "example": 2.5},
                    "physical_activity_level": {"type": "string", "example": "Moderate"},
                    "glasses_usage": {"type": "string", "example": "Yes"}
                }
            }
        }
    ],
    "responses": {
        "201": {
            "description": "Assessment completed",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "risk_level": {"type": "string", "example": "Medium"},
                    "confidence_score": {"type": "number", "example": 0.85},
                    "predicted_disease": {"type": "string", "example": "Dry Eye"},
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "400": {"description": "Missing required fields"}
    }
}

USER_PROFILE_SPEC = {
    "tags": ["User"],
    "summary": "Get user profile",
    "description": "Retrieve complete user profile including health records, habits, and latest assessment",
    "parameters": [
        {
            "name": "user_id",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "Unique user identifier"
        }
    ],
    "responses": {
        "200": {
            "description": "Profile retrieved successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                            "username": {"type": "string"},
                            "email": {"type": "string"},
                            "full_name": {"type": "string"}
                        }
                    },
                    "health": {"type": "object"},
                    "habit": {"type": "object"},
                    "assessment": {"type": "object"}
                }
            }
        },
        "404": {"description": "User not found"}
    }
}

PREDICT_SPEC = {
    "tags": ["Prediction"],
    "summary": "Get eye disease risk prediction",
    "description": "ML-powered prediction using LightGBM model and rule-based assessment",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["age", "screen_time", "sleep_hours", "diet_quality"],
                "properties": {
                    "age": {"type": "integer", "example": 35},
                    "screen_time": {"type": "number", "example": 8},
                    "sleep_hours": {"type": "number", "example": 6},
                    "diet_quality": {"type": "integer", "example": 3}
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Prediction generated",
            "schema": {
                "type": "object",
                "properties": {
                    "ml_prediction": {"type": "string", "example": "High"},
                    "rule_result": {"type": "string", "example": "Medium"}
                }
            }
        }
    }
}

NOTIFICATIONS_SPEC = {
    "tags": ["Notifications"],
    "summary": "Get user notifications",
    "description": "Fetch all notifications for a specific user",
    "parameters": [
        {
            "name": "user_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "User ID"
        }
    ],
    "responses": {
        "200": {
            "description": "Notifications retrieved",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "notifications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "notification_id": {"type": "string"},
                                "title": {"type": "string"},
                                "message": {"type": "string"},
                                "type": {"type": "string"},
                                "is_read": {"type": "boolean"}
                            }
                        }
                    },
                    "unread_count": {"type": "integer"}
                }
            }
        }
    }
}

FEEDBACK_SPEC = {
    "tags": ["Feedback"],
    "summary": "Submit user feedback",
    "description": "Submit feedback about the application with rating and comments",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["user_id", "username", "email", "rating", "category", "comment"],
                "properties": {
                    "user_id": {"type": "string", "example": "user_123"},
                    "username": {"type": "string", "example": "John Doe"},
                    "email": {"type": "string", "example": "john@example.com"},
                    "rating": {"type": "integer", "minimum": 1, "maximum": 5, "example": 5},
                    "category": {"type": "string", "example": "Assessment Accuracy"},
                    "comment": {"type": "string", "example": "Great app!"}
                }
            }
        }
    ],
    "responses": {
        "201": {"description": "Feedback submitted successfully"},
        "400": {"description": "Invalid rating or missing fields"}
    }
}
