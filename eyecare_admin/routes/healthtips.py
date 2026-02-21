from flask import Blueprint, request, jsonify, session
from database import db, HealthTip, ActivityLog, Admin
from datetime import datetime
from marshmallow import ValidationError
from schemas import HealthTipCreateSchema, HealthTipUpdateSchema
from utils.archive import archive_entity

healthtips_bp = Blueprint('healthtips', __name__)


def _require_login():
    if 'admin_id' not in session:
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    admin = Admin.query.get(session.get('admin_id'))
    if not admin:
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    return admin, None


def _require_super_admin(admin):
    if not admin or admin.role != 'super_admin':
        return jsonify({'error': 'Forbidden: requires super_admin (submit via approvals)'}), 403
    return None

@healthtips_bp.route('/', methods=['GET'])
def get_healthtips():
    try:
        admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        # Data analysts should not access Health Tips
        if admin.role in ['data_analyst', 'analyst']:
            return jsonify({'error': 'Forbidden'}), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Simple pagination
        query = HealthTip.query.order_by(HealthTip.created_at.desc())
        total = query.count()
        tips = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'healthtips': [tip.to_dict() for tip in tips],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@healthtips_bp.route('/<int:tip_id>', methods=['GET'])
def get_healthtip(tip_id):
    try:
        admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        if admin.role in ['data_analyst', 'analyst']:
            return jsonify({'error': 'Forbidden'}), 403

        tip = HealthTip.query.get_or_404(tip_id)
        return jsonify({'healthtip': tip.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@healthtips_bp.route('/', methods=['POST'])
def create_healthtip():
    try:
        from database import Admin, PendingAction
        import json
        
        # Check permissions
        current_admin = Admin.query.get(session.get('admin_id'))
        if not current_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        # Data analysts should not access Health Tips
        if current_admin.role in ['data_analyst', 'analyst']:
            return jsonify({'error': 'Forbidden'}), 403

        data = request.json
        
        # If not Super Admin, queue for approval
        if current_admin.role != 'super_admin':
            # Create pending action
            pending = PendingAction(
                requester_id=current_admin.id,
                action_type='create_health_tip',
                data=json.dumps(data),
                status='pending_admin' if current_admin.role in ['staff', 'data_analyst', 'analyst'] else 'pending_super_admin'
            )
            
            # Staff/Data Analyst -> Pending Admin
            # Admin -> Pending Super Admin
            if current_admin.role in ['staff', 'data_analyst', 'analyst']:
                pending.status = 'pending_admin'
            elif current_admin.role == 'admin':
                pending.status = 'pending_super_admin'
            
            db.session.add(pending)
            db.session.commit()
            
            return jsonify({'message': 'Health tip creation queued for approval'}), 202

        # If Super Admin, proceed directly
        tip_id = HealthTip.create(
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category')
        )
        tip = HealthTip.get_by_id(tip_id)
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Create Health Tip',
            entity_type='healthtip',
            entity_id=tip.id,
            details=f'Created health tip: {tip.title}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Health tip created successfully',
            'healthtip': tip.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@healthtips_bp.route('/<int:tip_id>', methods=['PUT'])
def update_healthtip(tip_id):
    try:
        admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        if admin.role in ['data_analyst', 'analyst']:
            return jsonify({'error': 'Forbidden'}), 403

        super_error = _require_super_admin(admin)
        if super_error:
            return super_error

        data = request.json
        
        # Update the health tip
        success = HealthTip.update(
            tip_id,
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category')
        )
        
        if not success:
            return jsonify({'error': 'Health tip not found or no changes made'}), 404
        
        # Log activity
        if 'admin_id' in session:
            log = ActivityLog(
                admin_id=session.get('admin_id'),
                action='Update Health Tip',
                entity_type='healthtip',
                entity_id=tip_id,
                details=f'Updated health tip: {data.get("title")}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        
        # Get updated tip
        updated_tip = HealthTip.get_by_id(tip_id)
        
        return jsonify({
            'message': 'Health tip updated successfully',
            'healthtip': updated_tip
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@healthtips_bp.route('/<int:tip_id>', methods=['DELETE'])
def delete_healthtip(tip_id):
    try:
        admin, auth_error = _require_login()
        if auth_error:
            return auth_error

        if admin.role in ['data_analyst', 'analyst']:
            return jsonify({'error': 'Forbidden'}), 403

        super_error = _require_super_admin(admin)
        if super_error:
            return super_error

        tip = HealthTip.query.get_or_404(tip_id)
        tip_title = tip.title

        archive_entity(
            entity_type='healthtip',
            entity_id=str(tip_id),
            data=tip.to_dict(),
            archived_by_admin_id=session.get('admin_id'),
            reason='Archived via admin delete endpoint',
        )

        db.session.delete(tip)
        db.session.commit()
        
        # Log activity
        if 'admin_id' in session:
            log = ActivityLog(
                admin_id=session.get('admin_id'),
                action='Delete Health Tip',
                entity_type='healthtip',
                entity_id=tip_id,
                details=f'Deleted health tip: {tip_title}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        
        return jsonify({'message': 'Health tip archived successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@healthtips_bp.route('/upload-image', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return jsonify({'error': 'Only image files allowed'}), 400
        
        # Save file
        import os
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        filepath = os.path.join('static', 'uploads', 'healthtips', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        image_url = f'/static/uploads/healthtips/{filename}'
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_url': image_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
