from flask import Blueprint, request, jsonify, session
from database import db, Admin, PendingAction, ActivityLog, AdminNotification
import json
from datetime import datetime, timedelta, timezone
from utils.archive import archive_entity

approvals_bp = Blueprint('approvals', __name__)

# Helper to check permissions
def get_current_admin():
    if 'admin_id' not in session:
        return None
    return Admin.query.get(session['admin_id'])

@approvals_bp.route('/', methods=['GET'])
def get_pending_approvals():
    """Get approvals based on role"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
        
    query = PendingAction.query
    
    if current_admin.role == 'super_admin':
        # Super Admin sees ALL requests pending super admin approval
        query = query.filter(PendingAction.status == 'pending_super_admin')
    elif current_admin.role == 'admin':
        # Admin sees requests from Data Analyst and Staff that need admin confirmation
        query = query.filter(PendingAction.status == 'pending_admin')
    else:
        # Data Analyst and Staff should not see this endpoint
        return jsonify({'error': 'Forbidden'}), 403
        
    approvals = query.order_by(PendingAction.created_at.desc()).all()
    return jsonify({'approvals': [a.to_dict() for a in approvals]}), 200

@approvals_bp.route('/my-requests', methods=['GET'])
def get_my_requests():
    """Get user's own submitted requests (for Data Analyst and Staff)"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
        
    requests = PendingAction.query.filter_by(requested_by=current_admin.id)\
        .order_by(PendingAction.created_at.desc()).all()
    
    return jsonify({'requests': [r.to_dict() for r in requests]}), 200

@approvals_bp.route('/<int:action_id>/confirm-forward', methods=['POST'])
def confirm_and_forward(action_id):
    """Admin confirms and forwards to Super Admin"""
    current_admin = get_current_admin()
    if not current_admin or current_admin.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
        
    action = PendingAction.query.get_or_404(action_id)
    
    if action.status != 'pending_admin':
        return jsonify({'error': 'Invalid action status'}), 400
    
    # Update status to pending_super_admin
    action.status = 'pending_super_admin'
    action.admin_reviewer_id = current_admin.id
    action.admin_reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    
    # Create notification for requester
    notification = AdminNotification(
        admin_id=action.requester_id,
        title='Request Forwarded',
        message=f'Your {action.action_type.replace("_", " ")} request has been forwarded to Super Admin for final approval.',
        type='info',
        link='/my-requests'
    )
    db.session.add(notification)
    
    # Create notification for all Super Admins
    super_admins = Admin.query.filter_by(role='super_admin').all()
    for super_admin in super_admins:
        notification = AdminNotification(
            admin_id=super_admin.id,
            title='New Request Awaiting Approval',
            message=f'{action.requester.full_name} submitted a {action.action_type.replace("_", " ")} request that requires your approval.',
            type='warning',
            link='/approvals'
        )
        db.session.add(notification)
    
    # Log
    log = ActivityLog(
        admin_id=current_admin.id,
        action='Confirm & Forward',
        entity_type='pending_action',
        entity_id=str(action.id),
        details=f'Admin confirmed {action.action_type} from {action.requester.full_name}, forwarded to Super Admin',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Request confirmed and forwarded to Super Admin'}), 200

@approvals_bp.route('/<int:action_id>/accept', methods=['POST'])
def accept_action(action_id):
    """Super Admin accepts and executes the action"""
    current_admin = get_current_admin()
    if not current_admin or current_admin.role != 'super_admin':
        return jsonify({'error': 'Unauthorized'}), 401
        
    action = PendingAction.query.get_or_404(action_id)
    
    if action.status != 'pending_super_admin':
        return jsonify({'error': 'Invalid action status'}), 400
    
    try:
        # Execute the action
        execute_action(action)
        
        # Update status
        action.status = 'approved'
        action.super_admin_id = current_admin.id
        action.super_admin_reviewed_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Log
        log = ActivityLog(
            admin_id=current_admin.id,
            action='Accept & Execute',
            entity_type='pending_action',
            entity_id=str(action.id),
            details=f'Super Admin accepted and executed {action.action_type} from {action.requester.full_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Notify requestor and admin reviewer
        notify_approval_success(action)
        
        return jsonify({'message': 'Action accepted and executed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Execution failed: {str(e)}'}), 500

@approvals_bp.route('/<int:action_id>/deny', methods=['POST'])
def deny_action(action_id):
    """Admin or Super Admin denies the request"""
    current_admin = get_current_admin()
    if not current_admin or current_admin.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json or {}
    reason = data.get('reason', 'No reason provided')
    
    action = PendingAction.query.get_or_404(action_id)
    
    # Update status
    action.status = 'rejected'
    action.rejection_reason = reason
    
    if current_admin.role == 'admin':
        action.admin_reviewer_id = current_admin.id
        action.admin_reviewed_at = datetime.now(timezone.utc)
    else:  # super_admin
        action.super_admin_id = current_admin.id
        action.super_admin_reviewed_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    # Log
    log = ActivityLog(
        admin_id=current_admin.id,
        action='Deny Request',
        entity_type='pending_action',
        entity_id=str(action.id),
        details=f'{current_admin.role} denied {action.action_type} from {action.requester.full_name}. Reason: {reason}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    # Notify requestor and admin reviewer (if exists)
    notify_denial(action, reason)
    
    return jsonify({'message': 'Request denied'}), 200

def execute_action(action):
    """Execute the approved action"""
    data = json.loads(action.data) if action.data else {}
    
    if action.action_type == 'retrain_model':
        # Import ml retraining logic
        # For now, just log it
        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Retrain Model',
            entity_type='ml_model',
            details=f'Model retrained by request from {action.requester.full_name}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()
        
    elif action.action_type == 'delete_user':
        from database import User
        user = User.query.get(action.target_id)
        if not user:
            raise ValueError('User not found')

        user.status = 'blocked'
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Block User',
            entity_type='user',
            entity_id=action.target_id,
            details=f'User {user.username} blocked',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'create_user':
        from database import User
        from werkzeug.security import generate_password_hash
        import random
        import string

        email = (data.get('email') or '').strip()
        full_name = (data.get('full_name') or '').strip()
        phone = (data.get('phone') or '').strip() or None

        if not email or not full_name:
            raise ValueError('Missing required fields for create_user')

        # Check for duplicates
        if User.query.filter_by(email=email).first() is not None:
            raise ValueError('User email already exists')

        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(chars) for _ in range(10))
        password_hash = generate_password_hash(password)

        user = User(
            username=email,
            full_name=full_name,
            email=email,
            phone_number=phone,
            status='active',
            password_hash=password_hash
        )
        db.session.add(user)
        db.session.commit()

        # Best-effort email
        try:
            from flask_mail import Message
            from app import mail
            msg = Message(
                "Welcome to EyeCare - Your Account Details",
                recipients=[email]
            )
            msg.body = f"""Hello {full_name},

Your account has been created successfully.

Username: {email}
Password: {password}

Please login and change your password immediately.

Regards,
EyeCare Admin Team
"""
            mail.send(msg)
        except Exception:
            pass

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Create User',
            entity_type='user',
            entity_id=user.id,
            details=f'User created: {user.full_name}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'update_user':
        from database import User
        user = User.query.get(action.target_id)
        if not user:
            raise ValueError('User not found')

        if 'full_name' in data:
            user.full_name = data.get('full_name')
        if 'email' in data and data.get('email'):
            user.email = data.get('email')
            user.username = data.get('email')
        if 'phone' in data:
            user.phone_number = data.get('phone')

        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Update User',
            entity_type='user',
            entity_id=action.target_id,
            details=f'User updated: {user.full_name}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'archive_user':
        from database import User
        user = User.query.get(action.target_id)
        if not user:
            raise ValueError('User not found')
        user.status = 'archived'
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Archive User',
            entity_type='user',
            entity_id=action.target_id,
            details=f'User archived: {user.full_name}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'restore_user':
        from database import User
        user = User.query.get(action.target_id)
        if not user:
            raise ValueError('User not found')
        user.status = 'active'
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Restore User',
            entity_type='user',
            entity_id=action.target_id,
            details=f'User restored: {user.full_name}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'block_user':
        from database import User
        user = User.query.get(action.target_id)
        if not user:
            raise ValueError('User not found')
        user.status = 'blocked'
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Block User',
            entity_type='user',
            entity_id=action.target_id,
            details=f'User blocked: {user.full_name}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'unblock_user':
        from database import User
        user = User.query.get(action.target_id)
        if not user:
            raise ValueError('User not found')
        user.status = 'active'
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Unblock User',
            entity_type='user',
            entity_id=action.target_id,
            details=f'User unblocked: {user.full_name}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'delete_user_permanent':
        from database import User, Assessment
        user = User.query.get(action.target_id)
        if not user:
            raise ValueError('User not found')

        archive_entity(
            entity_type='user',
            entity_id=str(action.target_id),
            data=user.to_dict(),
            archived_by_admin_id=action.super_admin_id,
            reason='Archived via approvals (execute delete_user_permanent)',
        )

        Assessment.query.filter_by(user_id=user.user_id).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Delete User Permanently',
            entity_type='user',
            entity_id=action.target_id,
            details='User permanently deleted',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()
            
    elif action.action_type == 'create_health_tip':
        from database import HealthTip

        tip = HealthTip(
            title=data.get('title'),
            description=data.get('content'),
            category=data.get('category', 'General'),
            icon=data.get('icon', 'info'),
            risk_level=data.get('risk_level', 'All'),
        )
        db.session.add(tip)
        db.session.commit()
        tip_id = tip.tip_id
        
        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Create Health Tip',
            entity_type='health_tip',
            entity_id=str(tip_id),
            details=f'Health tip created: {data.get("title")}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()
        
    elif action.action_type == 'update_health_tip':
        from database import HealthTip
        tip_id = int(action.target_id) if action.target_id is not None else None
        if not tip_id:
            raise ValueError('Missing target_id for update_health_tip')
        ok = HealthTip.update(
            tip_id,
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category')
        )
        if not ok:
            raise ValueError('Health tip not found')

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Update Health Tip',
            entity_type='health_tip',
            entity_id=str(tip_id),
            details=f'Health tip updated: {data.get("title")}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()
            
    elif action.action_type == 'delete_health_tip':
        from database import HealthTip
        tip_id = int(action.target_id) if action.target_id is not None else None
        if not tip_id:
            raise ValueError('Missing target_id for delete_health_tip')
        ok = HealthTip.delete(tip_id)
        if not ok:
            raise ValueError('Health tip not found')

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Delete Health Tip',
            entity_type='health_tip',
            entity_id=str(tip_id),
            details='Health tip deleted',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'create_admin':
        from database import Admin
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        full_name = (data.get('full_name') or '').strip()
        role = (data.get('role') or 'staff').strip()
        password = data.get('password')

        if not username or not email or not full_name:
            raise ValueError('Missing required fields for create_admin')

        if Admin.query.filter_by(username=username).first() is not None:
            raise ValueError('Username already exists')
        if Admin.query.filter_by(email=email).first() is not None:
            raise ValueError('Email already exists')

        admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            role='data_analyst' if role == 'analyst' else role,
            status='active'
        )
        if password:
            admin.set_password(password)
        else:
            admin.set_password('admin123')

        db.session.add(admin)
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Create Admin',
            entity_type='admin',
            entity_id=str(admin.id),
            details=f'Admin created: {admin.username}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'update_admin':
        from database import Admin
        admin = Admin.query.get(action.target_id)
        if not admin:
            raise ValueError('Admin not found')

        if 'full_name' in data and data.get('full_name'):
            admin.full_name = data.get('full_name')
        if 'email' in data and data.get('email'):
            admin.email = data.get('email')
        if 'role' in data and data.get('role'):
            role = data.get('role')
            admin.role = 'data_analyst' if role == 'analyst' else role
        if 'password' in data and data.get('password'):
            admin.set_password(data.get('password'))

        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Update Admin',
            entity_type='admin',
            entity_id=str(admin.id),
            details=f'Admin updated: {admin.username}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()

    elif action.action_type == 'delete_admin':
        from database import Admin
        admin = Admin.query.get(action.target_id)
        if not admin:
            raise ValueError('Admin not found')

        # Prevent deleting the acting super admin account
        if str(admin.id) == str(action.super_admin_id):
            raise ValueError('Cannot delete own account')

        username = admin.username
        archive_entity(
            entity_type='admin',
            entity_id=str(action.target_id),
            data=admin.to_dict(),
            archived_by_admin_id=action.super_admin_id,
            reason='Archived via approvals (execute delete_admin)',
        )

        admin.status = 'archived'
        db.session.commit()

        log = ActivityLog(
            admin_id=action.super_admin_id,
            action='Execute: Archive Admin',
            entity_type='admin',
            entity_id=str(action.target_id),
            details=f'Admin archived: {username}',
            ip_address='system'
        )
        db.session.add(log)
        db.session.commit()
    
    # Add more action types as needed

def notify_approval_success(action):
    """Send notifications when action is approved"""
    # Notify requestor
    notification1 = AdminNotification(
        admin_id=action.requester_id,
        title='Request Approved ✓',
        message=f'Your {action.action_type.replace("_", " ")} request has been approved and executed successfully.',
        type='success',
        link='/my-requests'
    )
    db.session.add(notification1)
    
    log1 = ActivityLog(
        admin_id=action.requester_id,
        action='Notification: Approved',
        entity_type='notification',
        entity_id=str(action.id),
        details=f'Your request for {action.action_type} has been approved and completed by Super Admin',
        ip_address='system'
    )
    db.session.add(log1)
    
    # Notify admin reviewer (if exists)
    if action.admin_reviewer_id:
        notification2 = AdminNotification(
            admin_id=action.admin_reviewer_id,
            title='Request Finalized',
            message=f'The {action.action_type.replace("_", " ")} request you reviewed has been approved by Super Admin.',
            type='info',
            link='/approvals'
        )
        db.session.add(notification2)
        
        log2 = ActivityLog(
            admin_id=action.admin_reviewer_id,
            action='Notification: Finalized',
            entity_type='notification',
            entity_id=str(action.id),
            details=f'Request for {action.action_type} that you reviewed has been finalized by Super Admin',
            ip_address='system'
        )
        db.session.add(log2)
    
    db.session.commit()

def notify_denial(action, reason):
    """Send notifications when action is denied"""
    # Notify requestor
    notification1 = AdminNotification(
        admin_id=action.requester_id,
        title='Request Denied',
        message=f'Your {action.action_type.replace("_", " ")} request has been denied. Reason: {reason}',
        type='error',
        link='/my-requests'
    )
    db.session.add(notification1)
    
    log1 = ActivityLog(
        admin_id=action.requester_id,
        action='Notification: Denied',
        entity_type='notification',
        entity_id=str(action.id),
        details=f'Your request for {action.action_type} has been denied. Reason: {reason}',
        ip_address='system'
    )
    db.session.add(log1)
    
    # Notify admin reviewer if super admin denied after admin approval
    if action.admin_reviewer_id and action.super_admin_id:
        notification2 = AdminNotification(
            admin_id=action.admin_reviewer_id,
            title='Request Denied by Super Admin',
            message=f'The {action.action_type.replace("_", " ")} request you approved was denied by Super Admin. Reason: {reason}',
            type='warning',
            link='/approvals'
        )
        db.session.add(notification2)
        
        log2 = ActivityLog(
            admin_id=action.admin_reviewer_id,
            action='Notification: Denied',
            entity_type='notification',
            entity_id=str(action.id),
            details=f'Request for {action.action_type} that you reviewed has been denied by Super Admin. Reason: {reason}',
            ip_address='system'
        )
        db.session.add(log2)
    
    db.session.commit()

@approvals_bp.route('/submit', methods=['POST'])
def submit_action():
    """Submit a new action for approval (for Admin, Data Analyst, Staff)"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    action_type = data.get('action_type')
    target_id = data.get('target_id')
    action_data = data.get('data', {})
    
    if not action_type:
        return jsonify({'error': 'action_type required'}), 400
    
    # Determine initial status based on role
    if current_admin.role == 'super_admin':
        # Super admin doesn't need approval - execute directly
        return jsonify({'error': 'Super admins execute actions directly'}), 400
    elif current_admin.role == 'admin':
        initial_status = 'pending_super_admin'  # Admin needs Super Admin approval
    else:  # data_analyst or staff
        initial_status = 'pending_admin'  # Need Admin first, then Super Admin
    
    # Create pending action
    action = PendingAction(
        requester_id=current_admin.id,
        action_type=action_type,
        target_id=target_id,
        data=json.dumps(action_data),
        status=initial_status
    )
    db.session.add(action)
    db.session.commit()
    
    # Log
    log = ActivityLog(
        admin_id=current_admin.id,
        action='Submit Request',
        entity_type='pending_action',
        entity_id=str(action.id),
        details=f'{current_admin.role} submitted request for {action_type}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Request submitted for approval',
        'action': action.to_dict()
    }), 201

@approvals_bp.route('/analytics', methods=['GET'])
def get_approval_analytics():
    """Get RBAC approval analytics"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from sqlalchemy import func, case
    from datetime import timedelta
    
    # Total approvals by status
    status_counts = db.session.query(
        PendingAction.status,
        func.count(PendingAction.id).label('count')
    ).group_by(PendingAction.status).all()
    
    status_stats = {
        'pending_admin': 0,
        'pending_super_admin': 0,
        'approved': 0,
        'rejected': 0
    }
    for status, count in status_counts:
        status_stats[status] = count
    
    # Action type breakdown
    action_counts = db.session.query(
        PendingAction.action_type,
        func.count(PendingAction.id).label('count')
    ).group_by(PendingAction.action_type).all()
    
    action_stats = [{'type': action, 'count': count} for action, count in action_counts]
    
    # Recent activity (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_activity = db.session.query(
        func.date(PendingAction.created_at).label('date'),
        func.count(PendingAction.id).label('count'),
        func.sum(case((PendingAction.status == 'approved', 1), else_=0)).label('approved'),
        func.sum(case((PendingAction.status == 'rejected', 1), else_=0)).label('rejected')
    ).filter(
        PendingAction.created_at >= week_ago
    ).group_by(func.date(PendingAction.created_at)).all()
    
    activity_data = [{
        'date': str(date),
        'total': count,
        'approved': int(approved),
        'rejected': int(rejected)
    } for date, count, approved, rejected in recent_activity]
    
    # Simplified approval time (just return 0 since super_admin_reviewed_at doesn't exist yet)
    avg_approval_hours = 0
    
    # Top requesters
    top_requesters = db.session.query(
        Admin.full_name,
        func.count(PendingAction.id).label('count')
    ).join(
        PendingAction, PendingAction.requested_by == Admin.id
    ).group_by(Admin.id).order_by(func.count(PendingAction.id).desc()).limit(5).all()
    
    requester_stats = [{'name': name, 'count': count} for name, count in top_requesters]
    
    return jsonify({
        'status_breakdown': status_stats,
        'action_breakdown': action_stats,
        'recent_activity': activity_data,
        'avg_approval_time_hours': avg_approval_hours,
        'top_requesters': requester_stats,
        'total_pending': status_stats['pending_admin'] + status_stats['pending_super_admin'],
        'total_completed': status_stats['approved'] + status_stats['rejected']
    }), 200
