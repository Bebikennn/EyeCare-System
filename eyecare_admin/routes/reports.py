from flask import Blueprint, request, jsonify, session, current_app, send_file
from database import db, User, Assessment, ActivityLog, Admin, HealthTip
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from utils.cache import cached, invalidate_cache
from utils.export import export_to_csv, export_to_excel, export_to_json
from io import BytesIO

reports_bp = Blueprint('reports', __name__)


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


@reports_bp.route('/dashboard-stats', methods=['GET'])
@cached(timeout=300, key_prefix='dashboard_stats')  # Cache for 5 minutes
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error
        
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(status='active').count()
        blocked_users = User.query.filter_by(status='blocked').count()
        
        # Assessment statistics
        total_assessments = Assessment.query.count()
        
        # Get assessments from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_assessments = Assessment.query.filter(
            Assessment.created_at >= thirty_days_ago
        ).count()
        
        # Risk level distribution
        risk_distribution = db.session.query(
            Assessment.risk_level,
            func.count(Assessment.assessment_id).label('count')
        ).group_by(Assessment.risk_level).all()
        
        risk_stats = {
            'low': 0,
            'moderate': 0,
            'high': 0
        }
        for risk_level, count in risk_distribution:
            if risk_level in risk_stats:
                risk_stats[risk_level] = count
        
        # Activity statistics
        total_activities = ActivityLog.query.count()
        recent_activities = ActivityLog.query.filter(
            ActivityLog.timestamp >= thirty_days_ago
        ).count()
        
        # Health tips statistics
        total_tips = HealthTip.query.count()
        active_tips = HealthTip.query.filter_by(is_active=True).count()
        
        # Recent user registrations (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_users = User.query.filter(
            User.created_at >= seven_days_ago
        ).count()
        
        return jsonify({
            'users': {
                'total': total_users,
                'active': active_users,
                'blocked': blocked_users,
                'recent_7_days': recent_users
            },
            'assessments': {
                'total': total_assessments,
                'recent_30_days': recent_assessments,
                'risk_distribution': risk_stats
            },
            'activities': {
                'total': total_activities,
                'recent_30_days': recent_activities
            },
            'health_tips': {
                'total': total_tips,
                'active': active_tips
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Dashboard stats error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/user-growth', methods=['GET'])
@cached(timeout=3600, key_prefix='user_growth')  # Cache for 1 hour
def get_user_growth():
    """Get user growth statistics over time"""
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error
        
        # Get days parameter (default 30)
        days = request.args.get('days', 30, type=int)
        
        if days > 365:
            days = 365  # Maximum 1 year
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get daily user registrations
        daily_registrations = db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.user_id).label('count')
        ).filter(
            User.created_at >= start_date
        ).group_by(
            func.date(User.created_at)
        ).order_by(
            func.date(User.created_at)
        ).all()
        
        # Format results
        growth_data = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            }
            for date, count in daily_registrations
        ]
        
        return jsonify({
            'period_days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'growth_data': growth_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'User growth error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/assessment-trends', methods=['GET'])
@cached(timeout=3600, key_prefix='assessment_trends')  # Cache for 1 hour
def get_assessment_trends():
    """Get assessment trends over time"""
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error
        
        days = request.args.get('days', 30, type=int)
        
        if days > 365:
            days = 365
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get daily assessment counts
        daily_assessments = db.session.query(
            func.date(Assessment.created_at).label('date'),
            func.count(Assessment.assessment_id).label('count')
        ).filter(
            Assessment.created_at >= start_date
        ).group_by(
            func.date(Assessment.created_at)
        ).order_by(
            func.date(Assessment.created_at)
        ).all()
        
        # Get risk level trends
        risk_trends = db.session.query(
            func.date(Assessment.created_at).label('date'),
            Assessment.risk_level,
            func.count(Assessment.assessment_id).label('count')
        ).filter(
            Assessment.created_at >= start_date
        ).group_by(
            func.date(Assessment.created_at),
            Assessment.risk_level
        ).order_by(
            func.date(Assessment.created_at)
        ).all()
        
        # Format results
        assessment_data = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            }
            for date, count in daily_assessments
        ]
        
        # Organize risk trends by date
        risk_data = {}
        for date, risk_level, count in risk_trends:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in risk_data:
                risk_data[date_str] = {'low': 0, 'moderate': 0, 'high': 0}
            if risk_level in risk_data[date_str]:
                risk_data[date_str][risk_level] = count
        
        return jsonify({
            'period_days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'assessment_data': assessment_data,
            'risk_trends': risk_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Assessment trends error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/activity-summary', methods=['GET'])
@cached(timeout=1800, key_prefix='activity_summary')  # Cache for 30 minutes
def get_activity_summary():
    """Get activity log summary"""
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error
        
        days = request.args.get('days', 7, type=int)
        
        if days > 90:
            days = 90
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get activity counts by action
        activity_counts = db.session.query(
            ActivityLog.action,
            func.count(ActivityLog.id).label('count')
        ).filter(
            ActivityLog.timestamp >= start_date
        ).group_by(
            ActivityLog.action
        ).order_by(
            func.count(ActivityLog.id).desc()
        ).all()
        
        # Get activity counts by admin
        admin_activity = db.session.query(
            Admin.username,
            func.count(ActivityLog.id).label('count')
        ).join(
            ActivityLog, ActivityLog.admin_id == Admin.id
        ).filter(
            ActivityLog.timestamp >= start_date
        ).group_by(
            Admin.username
        ).order_by(
            func.count(ActivityLog.id).desc()
        ).all()
        
        # Format results
        action_summary = [
            {'action': action, 'count': count}
            for action, count in activity_counts
        ]
        
        admin_summary = [
            {'username': username, 'count': count}
            for username, count in admin_activity
        ]
        
        return jsonify({
            'period_days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'actions': action_summary,
            'admins': admin_summary,
            'total_activities': sum(count for _, count in activity_counts)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Activity summary error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/top-users', methods=['GET'])
@cached(timeout=3600, key_prefix='top_users')  # Cache for 1 hour
def get_top_users():
    """Get users with most assessments"""
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error
        
        limit = request.args.get('limit', 10, type=int)
        
        if limit > 50:
            limit = 50
        
        # Get users with assessment counts
        top_users = db.session.query(
            User.user_id,
            User.email,
            User.first_name,
            User.last_name,
            func.count(Assessment.assessment_id).label('assessment_count')
        ).join(
            Assessment, Assessment.user_id == User.user_id
        ).group_by(
            User.user_id,
            User.email,
            User.first_name,
            User.last_name
        ).order_by(
            func.count(Assessment.assessment_id).desc()
        ).limit(limit).all()
        
        # Format results
        users_data = [
            {
                'user_id': user_id,
                'email': email,
                'full_name': f'{first_name} {last_name}',
                'assessment_count': count
            }
            for user_id, email, first_name, last_name, count in top_users
        ]
        
        return jsonify({
            'top_users': users_data,
            'limit': limit
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Top users error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/comprehensive', methods=['GET'])
def generate_comprehensive_report():
    """Generate a comprehensive report combining all metrics"""
    try:
        auth_error = _require_admin_or_super()
        if auth_error:
            return auth_error
        
        format_type = request.args.get('format', 'json').lower()
        
        if format_type not in ['json', 'csv', 'excel']:
            return jsonify({'error': 'Invalid format. Use json, csv, or excel'}), 400
        
        # Date range
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)
        else:
            end_date = datetime.now()
        
        # Summary statistics
        total_users = User.query.filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).count()
        
        total_assessments = Assessment.query.filter(
            Assessment.assessed_at >= start_date,
            Assessment.assessed_at <= end_date
        ).count()
        
        high_risk = Assessment.query.filter(
            Assessment.risk_level == 'high',
            Assessment.assessed_at >= start_date,
            Assessment.assessed_at <= end_date
        ).count()
        
        # Daily breakdown
        daily_stats = []
        current = start_date
        while current <= end_date:
            day_start = datetime.combine(current.date(), datetime.min.time())
            day_end = day_start + timedelta(days=1)
            
            users_count = User.query.filter(
                User.created_at >= day_start,
                User.created_at < day_end
            ).count()
            
            assessments_count = Assessment.query.filter(
                Assessment.assessed_at >= day_start,
                Assessment.assessed_at < day_end
            ).count()
            
            high_risk_count = Assessment.query.filter(
                Assessment.risk_level == 'high',
                Assessment.assessed_at >= day_start,
                Assessment.assessed_at < day_end
            ).count()
            
            daily_stats.append({
                'date': current.strftime('%Y-%m-%d'),
                'new_users': users_count,
                'assessments': assessments_count,
                'high_risk_assessments': high_risk_count
            })
            
            current += timedelta(days=1)
        
        report_data = {
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'summary': {
                'total_users': total_users,
                'total_assessments': total_assessments,
                'high_risk_assessments': high_risk,
                'high_risk_percentage': round((high_risk / total_assessments * 100) if total_assessments > 0 else 0, 1)
            },
            'daily_breakdown': daily_stats
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            filename = f'comprehensive_report_{timestamp}'
            json_content = export_to_json(report_data, filename)
            return send_file(
                BytesIO(json_content.encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'{filename}.json'
            )
        elif format_type == 'csv':
            # For CSV, flatten the daily breakdown
            filename = f'comprehensive_report_{timestamp}'
            columns = {
                'Date': 'date',
                'New Users': 'new_users',
                'Assessments': 'assessments',
                'High Risk': 'high_risk_assessments'
            }
            csv_content = export_to_csv(daily_stats, columns, filename)
            return send_file(
                BytesIO(csv_content.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{filename}.csv'
            )
        elif format_type == 'excel':
            filename = f'comprehensive_report_{timestamp}'
            columns = {
                'Date': 'date',
                'New Users': 'new_users',
                'Assessments': 'assessments',
                'High Risk': 'high_risk_assessments'
            }
            excel_content = export_to_excel(daily_stats, columns, filename)
            return send_file(
                excel_content,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'{filename}.xlsx'
            )
        
    except Exception as e:
        current_app.logger.error(f'Comprehensive report error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500
