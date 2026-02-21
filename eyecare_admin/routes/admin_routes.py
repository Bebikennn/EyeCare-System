from flask import Blueprint, request, jsonify, session
from database import db, Admin, ActivityLog, ArchivedEntity
from datetime import datetime
from marshmallow import ValidationError
from schemas import AdminCreateSchema, AdminUpdateSchema, PasswordChangeSchema
from utils import validate_password
from utils.archive import archive_entity
from sqlalchemy import cast, Integer

admin_bp = Blueprint('admin', __name__)


def _require_login():
    if 'admin_id' not in session:
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    admin = Admin.query.get(session.get('admin_id'))
    if not admin:
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    return admin, None

@admin_bp.route('/', methods=['GET'])
def get_admins():
    try:
        current_admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        if current_admin.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Forbidden'}), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        role = request.args.get('role', '')
        status = request.args.get('status', '').strip().lower()

        # IMPORTANT:
        # Some deployments have a legacy MySQL schema for `admins.status` that
        # does not accept the literal value 'archived' (it gets stored as '').
        # To make archiving reliable without DB migrations, we treat the
        # presence of an ArchivedEntity row for entity_type='admin' as the
        # source of truth for "archived" state.
        # Cast archived_entities.entity_id (stored as a string) to integer so we
        # can compare against admins.id without triggering MySQL collation
        # conflicts (e.g., "Illegal mix of collations" when casting admins.id
        # to CHAR).
        archived_id_subq = (
            db.session.query(cast(ArchivedEntity.entity_id, Integer))
            .filter(ArchivedEntity.entity_type == 'admin')
            .subquery()
        )

        query = Admin.query

        # Default: hide archived admins
        if status == 'archived':
            query = query.filter(Admin.id.in_(archived_id_subq))
        elif status == 'all':
            pass
        else:
            query = query.filter(~Admin.id.in_(archived_id_subq))
        
        if role:
            query = query.filter_by(role=role)
        
        query = query.order_by(Admin.created_at.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        admins_out = []
        if status == 'archived':
            for admin in paginated.items:
                d = admin.to_dict()
                d['status'] = 'archived'
                admins_out.append(d)
        elif status == 'all':
            ids = [str(a.id) for a in paginated.items]
            archived_ids = set(
                row[0]
                for row in (
                    db.session.query(ArchivedEntity.entity_id)
                    .filter(ArchivedEntity.entity_type == 'admin', ArchivedEntity.entity_id.in_(ids))
                    .all()
                )
            )
            for admin in paginated.items:
                d = admin.to_dict()
                if str(admin.id) in archived_ids:
                    d['status'] = 'archived'
                admins_out.append(d)
        else:
            admins_out = [admin.to_dict() for admin in paginated.items]

        return jsonify({
            'admins': admins_out,
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/<int:admin_id>', methods=['GET'])
def get_admin(admin_id):
    try:
        current_admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        if current_admin.role != 'super_admin' and current_admin.id != admin_id:
            return jsonify({'error': 'Forbidden'}), 403

        admin = Admin.query.get_or_404(admin_id)
        return jsonify({'admin': admin.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/', methods=['POST'])
def create_admin():
    try:
        current_admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        # Check if current user is super admin
        if current_admin.role != 'super_admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.json
        
        # Check if username or email already exists
        if Admin.query.filter_by(username=data.get('username')).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if Admin.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        admin = Admin(
            username=data.get('username'),
            email=data.get('email'),
            full_name=data.get('full_name'),
            role=data.get('role', 'staff'),
            status='active'
        )
        admin.set_password(data.get('password'))
        
        db.session.add(admin)
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Create Admin',
            entity_type='admin',
            entity_id=admin.id,
            details=f'Created admin account: {admin.username}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Admin created successfully',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/<int:admin_id>', methods=['PUT'])
def update_admin(admin_id):
    try:
        current_admin, auth_error = _require_login()
        if auth_error:
            return jsonify({'error': 'Unauthorized'}), 403

        # Only super admin can update other admin accounts
        if current_admin.role != 'super_admin' and current_admin.id != admin_id:
            return jsonify({'error': 'Forbidden'}), 403
        
        admin = Admin.query.get_or_404(admin_id)
        data = request.json
        
        # Only super admin can change roles
        if 'role' in data and current_admin.role != 'super_admin':
            return jsonify({'error': 'Only super admin can change roles'}), 403
        
        admin.full_name = data.get('full_name', admin.full_name)
        admin.email = data.get('email', admin.email)
        
        if 'role' in data and current_admin.role == 'super_admin':
            admin.role = data.get('role')
        
        if 'status' in data and current_admin.role == 'super_admin':
            admin.status = data.get('status')
        
        if 'password' in data and data.get('password'):
            admin.set_password(data.get('password'))
        
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Update Admin',
            entity_type='admin',
            entity_id=admin.id,
            details=f'Updated admin account: {admin.username}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Admin updated successfully',
            'admin': admin.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/<int:admin_id>', methods=['DELETE'])
def delete_admin(admin_id):
    try:
        current_admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        # Check if current user is super admin
        if current_admin.role != 'super_admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Prevent deleting own account
        if admin_id == current_admin.id:
            return jsonify({'error': 'Cannot delete own account'}), 400
        
        admin = Admin.query.get_or_404(admin_id)
        admin_username = admin.username

        archive_entity(
            entity_type='admin',
            entity_id=str(admin_id),
            data=admin.to_dict(),
            archived_by_admin_id=session.get('admin_id'),
            reason='Archived via admin delete endpoint',
        )

        # Use a value that the legacy MySQL schema reliably supports.
        # "archived" is represented by the archive snapshot + status inactive.
        admin.status = 'inactive'
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Archive Admin',
            entity_type='admin',
            entity_id=admin_id,
            details=f'Archived admin account: {admin_username}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Admin archived successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/<int:admin_id>/restore', methods=['POST'])
def restore_admin(admin_id):
    try:
        current_admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        # Check if current user is super admin
        if current_admin.role != 'super_admin':
            return jsonify({'error': 'Unauthorized'}), 403

        admin = Admin.query.get_or_404(admin_id)
        admin_username = admin.username

        archived_rows = ArchivedEntity.query.filter(
            ArchivedEntity.entity_type == 'admin',
            ArchivedEntity.entity_id == str(admin_id),
        ).all()

        if not archived_rows:
            return jsonify({'error': 'Admin is not archived'}), 400

        for row in archived_rows:
            db.session.delete(row)

        admin.status = 'active'
        db.session.commit()

        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Restore Admin',
            entity_type='admin',
            entity_id=admin_id,
            details=f'Restored admin account: {admin_username}',
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'message': 'Admin restored successfully', 'admin': admin.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get current admin's profile"""
    try:
        admin, auth_error = _require_login()
        if auth_error:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({'admin': admin.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update current admin's profile"""
    try:
        admin, auth_error = _require_login()
        if auth_error:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.json
        
        # Check if new email is already taken by another admin
        if 'email' in data and data.get('email') != admin.email:
            existing = Admin.query.filter_by(email=data.get('email')).first()
            if existing and existing.id != admin.id:
                return jsonify({'error': 'Email already in use'}), 400
            admin.email = data.get('email')
        
        if 'full_name' in data:
            admin.full_name = data.get('full_name')
        
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Update Profile',
            entity_type='admin',
            entity_id=admin.id,
            details='Updated own profile',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'admin': admin.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/change-password', methods=['POST'])
def change_password():
    try:
        admin, auth_error = _require_login()
        if auth_error:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not admin.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        admin.set_password(new_password)
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=admin.id,
            action='Change Password',
            entity_type='admin',
            entity_id=admin.id,
            details='Changed password',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/stats', methods=['GET'])
def get_admin_stats():
    try:
        total_admins = Admin.query.count()
        super_admins = Admin.query.filter_by(role='super_admin').count()
        analysts = Admin.query.filter_by(role='analyst').count()
        staff = Admin.query.filter_by(role='staff').count()
        
        return jsonify({
            'total_admins': total_admins,
            'super_admins': super_admins,
            'analysts': analysts,
            'staff': staff
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics including real ML metrics"""
    try:
        from database import User, Assessment, MLMetrics
        import json
        
        # Get user stats
        user_stats = User.get_stats()
        
        # Get assessment stats
        assessment_stats = Assessment.get_stats()
        
        # Get latest ML metrics (from train_lightgbm.py)
        latest_metrics = MLMetrics.query.order_by(MLMetrics.training_date.desc()).first()
        
        ml_stats = {
            'accuracy': 0,
            'model_version': 'Not trained',
            'dataset_size': 0
        }
        
        if latest_metrics:
            ml_stats = {
                'accuracy': latest_metrics.accuracy,
                'precision': latest_metrics.precision,
                'recall': latest_metrics.recall,
                'f1_score': latest_metrics.f1_score,
                'model_version': latest_metrics.model_version,
                'dataset_size': latest_metrics.dataset_size,
                'training_date': latest_metrics.training_date.isoformat() if latest_metrics.training_date else None
            }
        
        return jsonify({
            'users': user_stats,
            'assessments': assessment_stats,
            'ml_metrics': ml_stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
