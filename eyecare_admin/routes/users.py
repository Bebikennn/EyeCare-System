from flask import Blueprint, request, jsonify, session, current_app, send_file
from database import db, User, Assessment, ActivityLog, Admin
from datetime import datetime, timedelta
from flask_mail import Message
from marshmallow import ValidationError
from schemas import UserCreateSchema, UserUpdateSchema
from utils import validate_password
from utils.pagination import Pagination
from utils.search import SearchFilter, parse_sort_params, apply_sorting
from utils.export import export_to_csv, export_to_json, export_to_excel
from utils.cache import cached, invalidate_cache
import string
import random
from werkzeug.security import generate_password_hash
from io import BytesIO
from utils.date_range import parse_request_date_range
from utils.archive import archive_entity

users_bp = Blueprint('users', __name__)


def _require_login():
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return None


def _require_admin_or_super():
    auth_error = _require_login()
    if auth_error:
        return auth_error
    admin = Admin.query.get(session.get('admin_id'))
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    if admin.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Forbidden'}), 403
    return None


def _require_super_admin():
    auth_error = _require_login()
    if auth_error:
        return auth_error
    admin = Admin.query.get(session.get('admin_id'))
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 401
    if admin.role != 'super_admin':
        return jsonify({'error': 'Forbidden: requires super_admin (submit via approvals)'}), 403
    return None

@users_bp.route('/', methods=['GET'])
def get_users():
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error

        # Build search filter
        search_filter = SearchFilter(User.query)
        
        # Simple search implementation
        query = User.query
        search = request.args.get('search', '').strip()
        if search:
            query = query.filter(
                db.or_(
                    User.email.ilike(f'%{search}%'),
                    User.full_name.ilike(f'%{search}%'),
                    User.username.ilike(f'%{search}%')
                )
            )
        
        # Status filter (legacy-safe):
        # - treat NULL status as active
        # - compare status case-insensitively
        status = request.args.get('status', '').strip().lower()
        normalized_status = db.func.lower(db.func.coalesce(User.status, 'active'))
        if status:
            query = query.filter(normalized_status == status)
        else:
            # Default: hide archived users from the main list
            query = query.filter(normalized_status != 'archived')
        
        # Date range filter
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        if start_date:
            from datetime import datetime as dt
            start = dt.fromisoformat(start_date)
            query = query.filter(User.created_at >= start)
        if end_date:
            from datetime import datetime as dt
            end = dt.fromisoformat(end_date)
            query = query.filter(User.created_at <= end)
        
        # Apply sorting
        allowed_sort_columns = {
            'created_at': User.created_at,
            'username': User.username,
            'email': User.email,
            'full_name': User.full_name,
            'status': User.status
        }
        column, sort_order = parse_sort_params(
            allowed_sort_columns,
            'created_at',
            'desc'
        )
        query = query.order_by(column.desc() if sort_order == 'desc' else column.asc())
        
        # Paginate results
        pagination = Pagination(query)
        
        # Convert users to dict
        users = [user.to_dict() for user in pagination.items]
        
        return jsonify({
            'users': users,
            'pagination': pagination.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Get users error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error

        user = User.query.get_or_404(user_id)
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/', methods=['POST'])
def create_user():
    try:
        auth_error = _require_super_admin()
        if auth_error:
            return auth_error

        data = request.json
        
        # Validate input
        schema = UserCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
        
        # Validate password strength
        password = validated_data.get('password')
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({'error': msg}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=validated_data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=validated_data['username']).first()
        if existing_username:
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create user with validated data
        password_hash = generate_password_hash(password)
        
        user = User(
            username=validated_data['username'],
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number'),
            status='active',
            password_hash=password_hash
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Send Email
        try:
            from app import mail
            msg = Message("Welcome to EyeCare - Your Account Details",
                          recipients=[user.email])
            msg.body = f"""
            Hello {user.full_name},
            
            Your account has been created successfully.
            
            Username: {user.username}
            Password: {password}
            
            Please login and change your password immediately.
            
            Regards,
            EyeCare Admin Team
            """
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email: {e}")
            # Don't fail the request, just log it
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Create User',
            entity_type='user',
            entity_id=user.id,
            details=f'Created user: {user.full_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Invalidate user stats cache
        invalidate_cache('user_stats')
        
        return jsonify({
            'message': 'User created successfully. Email sent.',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        auth_error = _require_super_admin()
        if auth_error:
            return auth_error

        user = User.query.get_or_404(user_id)
        data = request.json
        
        user.full_name = data.get('full_name', user.full_name)
        user.email = data.get('email', user.email)
        user.phone_number = data.get('phone', user.phone_number)
        # Age/Gender are not in users table, ignoring for now or need to update health_records
        
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Update User',
            entity_type='user',
            entity_id=user.user_id,
            details=f'Updated user: {user.full_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        auth_error = _require_super_admin()
        if auth_error:
            return auth_error

        user = User.query.get_or_404(user_id)
        user_name = user.full_name
        
        # Soft delete (archive)
        archive_entity(
            entity_type='user',
            entity_id=str(user_id),
            data=user.to_dict(),
            archived_by_admin_id=session.get('admin_id'),
            reason='Archived via admin delete endpoint',
        )

        user.status = 'archived'
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Archive User',
            entity_type='user',
            entity_id=user_id,
            details=f'Archived user: {user_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'User archived successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/archived', methods=['GET'])
def get_archived_users():
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error

        query = User.query.filter_by(status='archived').order_by(User.created_at.desc())
        pagination = Pagination(query)

        users = [user.to_dict() for user in pagination.items]

        return jsonify({
            'users': users,
            'pagination': pagination.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>/restore', methods=['POST'])
def restore_user(user_id):
    try:
        auth_error = _require_super_admin()
        if auth_error:
            return auth_error

        user = User.query.get_or_404(user_id)
        user.status = 'active'
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Restore User',
            entity_type='user',
            entity_id=user.user_id,
            details=f'Restored user: {user.full_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'User restored successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>/permanent', methods=['DELETE'])
def delete_user_permanently(user_id):
    try:
        auth_error = _require_super_admin()
        if auth_error:
            return auth_error

        user = User.query.get_or_404(user_id)
        user_name = user.full_name or user.username

        archive_entity(
            entity_type='user',
            entity_id=str(user_id),
            data=user.to_dict(),
            archived_by_admin_id=session.get('admin_id'),
            reason='Archived via permanent delete endpoint (pre-delete snapshot)',
        )

        # Delete assessments first to avoid FK issues
        Assessment.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Delete User Permanently',
            entity_type='user',
            entity_id=user_id,
            details=f'Permanently deleted user: {user_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'User permanently deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>/block', methods=['POST'])
def block_user(user_id):
    try:
        auth_error = _require_super_admin()
        if auth_error:
            return auth_error

        user = User.query.get_or_404(user_id)
        user.status = 'blocked'
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Block User',
            entity_type='user',
            entity_id=user.user_id,
            details=f'Blocked user: {user.full_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'User blocked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>/unblock', methods=['POST'])
def unblock_user(user_id):
    try:
        auth_error = _require_super_admin()
        if auth_error:
            return auth_error

        user = User.query.get_or_404(user_id)
        user.status = 'active'
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Unblock User',
            entity_type='user',
            entity_id=user.user_id,
            details=f'Unblocked user: {user.full_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'User unblocked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<string:user_id>/assessments', methods=['GET'])
def get_user_assessments(user_id):
    try:
        user = User.query.get_or_404(user_id)
        assessments = Assessment.query.filter_by(user_id=user_id).order_by(Assessment.created_at.desc()).all()
        
        return jsonify({
            'user': user.to_dict(),
            'assessments': [assessment.to_dict() for assessment in assessments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/stats', methods=['GET'])
@cached(timeout=300, key_prefix='user_stats')  # Cache for 5 minutes
def get_user_stats():
    try:
        date_range = parse_request_date_range(default_days=30)

        total_users = User.query.count()
        active_users = User.query.filter_by(status='active').count()
        blocked_users = User.query.filter_by(status='blocked').count()
        archived_users = User.query.filter_by(status='archived').count()

        # Users created during selected range
        recent_users_count = User.query.filter(
            User.created_at >= date_range.start,
            User.created_at < date_range.end_exclusive,
        ).count()

        # Growth vs previous period of same length
        previous_start = date_range.start - timedelta(days=date_range.days)
        previous_end = date_range.start

        current_period_users = recent_users_count
        previous_period_users = User.query.filter(
            User.created_at >= previous_start,
            User.created_at < previous_end,
        ).count()
        
        if previous_period_users > 0:
            growth_percentage = round(((current_period_users - previous_period_users) / previous_period_users) * 100, 1)
        else:
            growth_percentage = 0.0
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'archived_users': archived_users,
            'recent_users_in_range': recent_users_count,
            'growth_percentage': growth_percentage
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Get user stats error: {str(e)}', exc_info=True)
        error_msg = str(e)
        if 'date' in error_msg or 'days' in error_msg:
            return jsonify({'error': error_msg}), 400
        return jsonify({'error': error_msg}), 500

@users_bp.route('/recent', methods=['GET'])
def get_recent_users():
    try:
        date_range = parse_request_date_range(default_days=30)
        limit = request.args.get('limit', 5, type=int)
        users = (
            User.query.filter(User.status != 'archived')
            .filter(User.created_at >= date_range.start, User.created_at < date_range.end_exclusive)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )
        return jsonify({'users': [user.to_dict() for user in users]}), 200
        
    except Exception as e:
        error_msg = str(e)
        if 'date' in error_msg or 'days' in error_msg:
            return jsonify({'error': error_msg}), 400
        return jsonify({'error': error_msg}), 500

@users_bp.route('/export', methods=['GET'])
def export_users():
    """Export users data in various formats (CSV, JSON, Excel)"""
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error
        
        # Get format parameter
        format_type = request.args.get('format', 'csv').lower()
        
        if format_type not in ['csv', 'json', 'excel']:
            return jsonify({'error': 'Invalid format. Use csv, json, or excel'}), 400
        
        # Build search filter (same as get_users)
        search_filter = SearchFilter(User.query)
        
        search = request.args.get('search', '').strip()
        if search:
            search_filter.add_text_search(search, ['email', 'first_name', 'last_name'])
        
        status = request.args.get('status', '').strip()
        if status:
            search_filter.add_exact_match('status', status)
        
        gender = request.args.get('gender', '').strip()
        if gender:
            search_filter.add_exact_match('gender', gender)
        
        min_age = request.args.get('min_age', type=int)
        max_age = request.args.get('max_age', type=int)
        if min_age is not None or max_age is not None:
            search_filter.add_range_filter('age', min_age, max_age)
        
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        if start_date or end_date:
            search_filter.add_date_range('created_at', start_date, end_date)
        
        query = search_filter.build()
        
        # Apply sorting
        sort_by, sort_order = parse_sort_params(
            request.args.get('sort_by', 'created_at'),
            request.args.get('sort_order', 'desc')
        )
        query = apply_sorting(query, User, sort_by, sort_order)
        
        # Get all users (no pagination for export)
        users = query.all()
        
        # Convert to dict
        users_data = [user.to_dict() for user in users]
        
        # Define columns for export
        columns = [
            'user_id', 'email', 'first_name', 'last_name', 'age', 'gender',
            'status', 'created_at', 'updated_at'
        ]
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'users_export_{timestamp}'
        
        # Export based on format
        if format_type == 'csv':
            file_content = export_to_csv(users_data, columns, filename)
            return send_file(
                BytesIO(file_content.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{filename}.csv'
            )
        elif format_type == 'json':
            file_content = export_to_json(users_data, filename)
            return send_file(
                BytesIO(file_content.encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'{filename}.json'
            )
        elif format_type == 'excel':
            file_content = export_to_excel(users_data, columns, filename)
            return send_file(
                file_content,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'{filename}.xlsx'
            )
        
        # Log export activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Export Users',
            entity_type='user',
            details=f'Exported {len(users_data)} users as {format_type}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f'Export users error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500