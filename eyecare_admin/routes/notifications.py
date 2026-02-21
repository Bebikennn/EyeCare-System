from flask import Blueprint, request, jsonify, session
from database import db, Admin, AdminNotification
from datetime import datetime
from utils.archive import archive_entity

notifications_bp = Blueprint('notifications', __name__)

def get_current_admin():
    if 'admin_id' not in session:
        return None
    return Admin.query.get(session['admin_id'])

@notifications_bp.route('/', methods=['GET'])
def get_notifications():
    """Get notifications for current admin"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get limit from query params
    limit = request.args.get('limit', 50, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = AdminNotification.query.filter_by(admin_id=current_admin.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(AdminNotification.created_at.desc()).limit(limit).all()
    
    # Get unread count
    unread_count = AdminNotification.query.filter_by(
        admin_id=current_admin.id, 
        is_read=False
    ).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count
    }), 200

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
def mark_as_read(notification_id):
    """Mark a notification as read"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    notification = AdminNotification.query.filter_by(
        id=notification_id, 
        admin_id=current_admin.id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Marked as read'}), 200

@notifications_bp.route('/read-all', methods=['POST'])
def mark_all_as_read():
    """Mark all notifications as read"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    AdminNotification.query.filter_by(
        admin_id=current_admin.id, 
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    return jsonify({'message': 'All notifications marked as read'}), 200

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    notification = AdminNotification.query.filter_by(
        id=notification_id, 
        admin_id=current_admin.id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    archive_entity(
        entity_type='admin_notification',
        entity_id=str(notification.id),
        data=notification.to_dict(),
        archived_by_admin_id=current_admin.id,
        reason='Archived via notification delete endpoint',
    )

    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'}), 200

@notifications_bp.route('/clear-all', methods=['DELETE'])
def clear_all_notifications():
    """Clear all notifications for current admin"""
    current_admin = get_current_admin()
    if not current_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    notifications = AdminNotification.query.filter_by(admin_id=current_admin.id).all()
    if notifications:
        archive_entity(
            entity_type='admin_notification_clear_all',
            entity_id=str(current_admin.id),
            data={
                'admin_id': current_admin.id,
                'cleared_count': len(notifications),
                'notification_ids': [n.id for n in notifications],
            },
            archived_by_admin_id=current_admin.id,
            reason='Archived via notification clear-all endpoint',
        )

        for n in notifications:
            db.session.delete(n)
        db.session.commit()
    else:
        db.session.commit()
    
    return jsonify({'message': 'All notifications cleared'}), 200

def create_notification(admin_id, title, message, notification_type='info', link=None):
    """Helper function to create a notification"""
    notification = AdminNotification(
        admin_id=admin_id,
        title=title,
        message=message,
        type=notification_type,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    return notification
