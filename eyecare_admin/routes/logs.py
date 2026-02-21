from flask import Blueprint, request, jsonify, session
from database import db, ActivityLog, Admin
from datetime import datetime, timedelta, timezone
from utils.date_range import parse_request_date_range

logs_bp = Blueprint('logs', __name__)


def _require_admin_or_super():
    if 'admin_id' not in session:
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    admin = Admin.query.get(session.get('admin_id'))
    if not admin:
        return None, (jsonify({'error': 'Unauthorized'}), 401)
    if admin.role not in ['admin', 'super_admin']:
        return None, (jsonify({'error': 'Forbidden'}), 403)
    return admin, None

@logs_bp.route('/', methods=['GET'])
def get_logs():
    try:
        _, auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        action = request.args.get('action', '')
        entity_type = request.args.get('entity_type', '')
        admin_id = request.args.get('admin_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        query = ActivityLog.query
        
        if action:
            query = query.filter(ActivityLog.action.ilike(f'%{action}%'))
        
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        
        if admin_id:
            query = query.filter_by(admin_id=admin_id)
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(ActivityLog.created_at >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(ActivityLog.created_at <= end)
        
        query = query.order_by(ActivityLog.created_at.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'logs': [log.to_dict() for log in paginated.items],
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@logs_bp.route('/recent', methods=['GET'])
def get_recent_logs():
    try:
        _, auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error

        date_range = parse_request_date_range(default_days=30)
        limit = request.args.get('limit', 10, type=int)

        logs = (
            ActivityLog.query.filter(
                ActivityLog.created_at >= date_range.start,
                ActivityLog.created_at < date_range.end_exclusive,
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs]
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        if 'date' in error_msg or 'days' in error_msg:
            return jsonify({'error': error_msg}), 400
        return jsonify({'error': error_msg}), 500

@logs_bp.route('/stats', methods=['GET'])
def get_log_stats():
    try:
        _, auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error

        # Activity by action type
        from sqlalchemy import func
        
        activity_by_action = db.session.query(
            ActivityLog.action,
            func.count(ActivityLog.id).label('count')
        ).group_by(ActivityLog.action).order_by(func.count(ActivityLog.id).desc()).limit(10).all()
        
        # Activity today
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time())
        activity_today = ActivityLog.query.filter(ActivityLog.created_at >= today_start).count()
        
        # Activity this week
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        activity_week = ActivityLog.query.filter(ActivityLog.created_at >= week_start).count()
        
        return jsonify({
            'activity_by_action': [{'action': action, 'count': count} for action, count in activity_by_action],
            'activity_today': activity_today,
            'activity_week': activity_week
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@logs_bp.route('/export', methods=['GET'])
def export_logs():
    try:
        _, auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error

        import csv
        import io
        
        logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Admin', 'Action', 'Entity Type', 'Entity ID', 
            'Details', 'IP Address', 'Timestamp'
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.id,
                log.admin.full_name if log.admin else 'System',
                log.action,
                log.entity_type,
                log.entity_id,
                log.details,
                log.ip_address,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=activity_logs.csv'
        }
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
