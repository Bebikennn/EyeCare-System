"""
API Documentation Configuration

This module provides Swagger/OpenAPI documentation for the EyeCare Admin API.
Access the interactive documentation at: /api/docs
"""

from flask import Blueprint
from flask_restx import Api, Resource, fields, Namespace

# Create documentation blueprint
docs_bp = Blueprint('docs', __name__)

# Initialize API with documentation
api = Api(
    docs_bp,
    version='1.0',
    title='EyeCare Admin API',
    description='Comprehensive API for EyeCare Admin Panel - User Management, Assessments, Health Tips, and Analytics',
    doc='/docs',
    prefix='/api'
)

# Define namespaces
auth_ns = api.namespace('auth', description='Authentication operations')
users_ns = api.namespace('users', description='User management operations')
assessments_ns = api.namespace('assessments', description='Assessment operations')
healthtips_ns = api.namespace('healthtips', description='Health tips management')
reports_ns = api.namespace('reports', description='Analytics and reporting')
admin_ns = api.namespace('admin', description='Admin management')
logs_ns = api.namespace('logs', description='Activity logs')

# Define models for documentation
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Admin username'),
    'password': fields.String(required=True, description='Admin password')
})

user_model = api.model('User', {
    'user_id': fields.String(description='User unique ID'),
    'email': fields.String(required=True, description='User email address'),
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
    'age': fields.Integer(description='Age'),
    'gender': fields.String(description='Gender'),
    'status': fields.String(description='Account status')
})

assessment_model = api.model('Assessment', {
    'assessment_id': fields.String(description='Assessment unique ID'),
    'user_id': fields.String(required=True, description='User ID'),
    'risk_level': fields.String(description='Risk level: low, moderate, high'),
    'risk_score': fields.Float(description='Risk score'),
    'created_at': fields.DateTime(description='Creation timestamp')
})

healthtip_model = api.model('HealthTip', {
    'tip_id': fields.String(description='Health tip unique ID'),
    'title': fields.String(required=True, description='Tip title'),
    'content': fields.String(required=True, description='Tip content'),
    'category': fields.String(description='Tip category'),
    'is_active': fields.Boolean(description='Active status')
})

pagination_model = api.model('Pagination', {
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page'),
    'total': fields.Integer(description='Total items'),
    'pages': fields.Integer(description='Total pages'),
    'has_prev': fields.Boolean(description='Has previous page'),
    'has_next': fields.Boolean(description='Has next page')
})

# Auth endpoints documentation
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login')
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful')
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Login to admin panel"""
        pass


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('logout')
    @auth_ns.response(200, 'Logout successful')
    def post(self):
        """Logout from admin panel"""
        pass


@auth_ns.route('/send-verification-email')
class SendVerificationEmail(Resource):
    @auth_ns.doc('send_verification_email')
    @auth_ns.response(200, 'Verification email sent')
    @auth_ns.response(401, 'Not authenticated')
    def post(self):
        """Send email verification link"""
        pass


@auth_ns.route('/verify-email')
class VerifyEmail(Resource):
    @auth_ns.doc('verify_email')
    @auth_ns.response(200, 'Email verified')
    @auth_ns.response(400, 'Invalid token')
    def post(self):
        """Verify email with token"""
        pass


# Users endpoints documentation
@users_ns.route('/')
class UserList(Resource):
    @users_ns.doc('list_users')
    @users_ns.param('page', 'Page number')
    @users_ns.param('per_page', 'Items per page')
    @users_ns.param('search', 'Search query')
    @users_ns.param('status', 'Filter by status')
    @users_ns.param('gender', 'Filter by gender')
    @users_ns.param('min_age', 'Minimum age')
    @users_ns.param('max_age', 'Maximum age')
    @users_ns.param('sort_by', 'Sort field')
    @users_ns.param('sort_order', 'Sort order (asc/desc)')
    @users_ns.response(200, 'Success')
    def get(self):
        """List all users with pagination and filtering"""
        pass

    @users_ns.doc('create_user')
    @users_ns.expect(user_model)
    @users_ns.response(201, 'User created')
    @users_ns.response(400, 'Validation error')
    def post(self):
        """Create new user"""
        pass


@users_ns.route('/export')
class UserExport(Resource):
    @users_ns.doc('export_users')
    @users_ns.param('format', 'Export format: csv, json, excel')
    @users_ns.param('search', 'Search query')
    @users_ns.param('status', 'Filter by status')
    @users_ns.response(200, 'Export successful')
    def get(self):
        """Export users data"""
        pass


@users_ns.route('/stats')
class UserStats(Resource):
    @users_ns.doc('user_stats')
    @users_ns.response(200, 'Success')
    def get(self):
        """Get user statistics"""
        pass


# Reports endpoints documentation
@reports_ns.route('/dashboard-stats')
class DashboardStats(Resource):
    @reports_ns.doc('dashboard_stats')
    @reports_ns.response(200, 'Success')
    def get(self):
        """Get comprehensive dashboard statistics"""
        pass


@reports_ns.route('/user-growth')
class UserGrowth(Resource):
    @reports_ns.doc('user_growth')
    @reports_ns.param('days', 'Number of days (default 30, max 365)')
    @reports_ns.response(200, 'Success')
    def get(self):
        """Get user growth over time"""
        pass


@reports_ns.route('/assessment-trends')
class AssessmentTrends(Resource):
    @reports_ns.doc('assessment_trends')
    @reports_ns.param('days', 'Number of days (default 30, max 365)')
    @reports_ns.response(200, 'Success')
    def get(self):
        """Get assessment trends over time"""
        pass


@reports_ns.route('/activity-summary')
class ActivitySummary(Resource):
    @reports_ns.doc('activity_summary')
    @reports_ns.param('days', 'Number of days (default 7, max 90)')
    @reports_ns.response(200, 'Success')
    def get(self):
        """Get activity log summary"""
        pass


@reports_ns.route('/top-users')
class TopUsers(Resource):
    @reports_ns.doc('top_users')
    @reports_ns.param('limit', 'Number of users (default 10, max 50)')
    @reports_ns.response(200, 'Success')
    def get(self):
        """Get users with most assessments"""
        pass


# Assessments endpoints documentation
@assessments_ns.route('/')
class AssessmentList(Resource):
    @assessments_ns.doc('list_assessments')
    @assessments_ns.param('page', 'Page number')
    @assessments_ns.param('per_page', 'Items per page')
    @assessments_ns.response(200, 'Success')
    def get(self):
        """List all assessments"""
        pass


# Health tips endpoints documentation
@healthtips_ns.route('/')
class HealthTipList(Resource):
    @healthtips_ns.doc('list_healthtips')
    @healthtips_ns.response(200, 'Success')
    def get(self):
        """List all health tips"""
        pass

    @healthtips_ns.doc('create_healthtip')
    @healthtips_ns.expect(healthtip_model)
    @healthtips_ns.response(201, 'Health tip created')
    def post(self):
        """Create new health tip"""
        pass


# Admin endpoints documentation
@admin_ns.route('/')
class AdminList(Resource):
    @admin_ns.doc('list_admins')
    @admin_ns.response(200, 'Success')
    def get(self):
        """List all admins"""
        pass


# Logs endpoints documentation
@logs_ns.route('/')
class LogList(Resource):
    @logs_ns.doc('list_logs')
    @logs_ns.param('page', 'Page number')
    @logs_ns.param('per_page', 'Items per page')
    @logs_ns.response(200, 'Success')
    def get(self):
        """List all activity logs"""
        pass
