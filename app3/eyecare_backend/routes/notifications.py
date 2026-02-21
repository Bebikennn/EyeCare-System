from flask import Blueprint, request, jsonify
from services.db import get_connection
from datetime import datetime, timezone
import uuid

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/user/<user_id>', methods=['GET'])
def get_user_notifications(user_id):
    """Fetch all notifications for a user"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Get all notifications ordered by most recent first
            cur.execute("""
                SELECT notification_id, title, message, type, is_read, link, created_at
                FROM user_notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id,))
            
            notifications = []
            for row in cur.fetchall():
                notifications.append({
                    'notification_id': row['notification_id'],
                    'title': row['title'],
                    'message': row['message'],
                    'type': row['type'],
                    'is_read': row['is_read'],
                    'link': row['link'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                })
            
            # Get unread count
            cur.execute("""
                SELECT COUNT(*) as unread FROM user_notifications
                WHERE user_id = %s AND is_read = 0
            """, (user_id,))
            result = cur.fetchone()
            unread_count = result['unread'] if result else 0
            
            # Debug logging
            print(f"🔔 Fetching notifications for user: {user_id}")
            print(f"📊 Found {len(notifications)} notification(s)")
            
            return jsonify({
                'status': 'success',
                'notifications': notifications,
                'unread_count': unread_count
            }), 200
    except Exception as e:
        import traceback
        print(f"❌ Error fetching notifications: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()

@notifications_bp.route('/user/<user_id>/<notification_id>/mark-read', methods=['PUT'])
def mark_notification_read(user_id, notification_id):
    """Mark a notification as read"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_notifications
                SET is_read = 1
                WHERE notification_id = %s AND user_id = %s
            """, (notification_id, user_id))
            conn.commit()
            
        return jsonify({
            'status': 'success',
            'message': 'Notification marked as read'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()

@notifications_bp.route('/user/<user_id>/mark-all-read', methods=['PUT'])
def mark_all_notifications_read(user_id):
    """Mark all notifications as read"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_notifications
                SET is_read = 1
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()
            updated_count = cur.rowcount
            
        return jsonify({
            'status': 'success',
            'message': 'All notifications marked as read',
            'updated_count': updated_count
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()

@notifications_bp.route('/user/<user_id>/create', methods=['POST'])
def create_notification(user_id):
    """Create a new notification for a user (admin use)"""
    conn = None
    try:
        data = request.get_json()
        
        title = data.get('title')
        message = data.get('message')
        notif_type = data.get('type', 'info')  # info, success, warning, error
        link = data.get('link')
        
        if not title or not message:
            return jsonify({
                'status': 'error',
                'error': 'Title and message are required'
            }), 400
        
        notification_id = str(uuid.uuid4())
        conn = get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_notifications
                (notification_id, user_id, title, message, type, is_read, link, created_at)
                VALUES (%s, %s, %s, %s, %s, 0, %s, %s)
            """, (notification_id, user_id, title, message, notif_type, link, datetime.now(timezone.utc)))
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'notification_id': notification_id,
            'message': 'Notification created'
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()
