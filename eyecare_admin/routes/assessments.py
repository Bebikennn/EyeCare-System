from flask import Blueprint, request, jsonify, session
from database import db, Assessment, User, ActivityLog
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from utils.cache import cached, invalidate_cache
from utils.date_range import parse_request_date_range
from utils.archive import archive_entity

assessments_bp = Blueprint('assessments', __name__)


def _parse_datetime_param(value: str, *, end_of_day: bool) -> datetime | None:
    if not value:
        return None
    v = value.strip()
    if not v:
        return None

    # Support common "Z" UTC suffix.
    if v.endswith('Z'):
        v = v[:-1] + '+00:00'

    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None

    # Normalize timezone-aware values to naive UTC for DB comparisons.
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

    # If it's date-only (no time), expand to day bounds.
    if 'T' not in v and len(v) <= 10:
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)

    return dt

@assessments_bp.route('/', methods=['GET'])
def get_assessments():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        risk_level = request.args.get('risk_level', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        user_id = request.args.get('user_id', '')

        start_dt = _parse_datetime_param(start_date, end_of_day=False) if start_date else None
        end_dt = _parse_datetime_param(end_date, end_of_day=True) if end_date else None

        if start_date and start_dt is None:
            return jsonify({'error': 'Invalid start_date. Use YYYY-MM-DD or ISO 8601 datetime.'}), 400
        if end_date and end_dt is None:
            return jsonify({'error': 'Invalid end_date. Use YYYY-MM-DD or ISO 8601 datetime.'}), 400
        
        # Build query
        query = Assessment.query
        
        if risk_level:
            query = query.filter_by(risk_level=risk_level)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if start_dt:
            query = query.filter(Assessment.assessed_at >= start_dt)
        if end_dt:
            query = query.filter(Assessment.assessed_at <= end_dt)
        
        query = query.order_by(Assessment.assessed_at.desc())
        
        # Paginate
        total = query.count()
        assessments = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'assessments': [a.to_dict() for a in assessments],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/<string:assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    try:
        assessment = Assessment.query.get_or_404(assessment_id)
        return jsonify({'assessment': assessment.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/', methods=['POST'])
def create_assessment():
    try:
        data = request.json
        
        assessment = Assessment(
            user_id=data.get('user_id'),
            age=data.get('age'),
            bmi=data.get('bmi'),
            blood_pressure=data.get('blood_pressure'),
            blood_sugar=data.get('blood_sugar'),
            smoking=data.get('smoking', False),
            alcohol=data.get('alcohol', False),
            screen_time=data.get('screen_time'),
            sleep_hours=data.get('sleep_hours'),
            exercise_frequency=data.get('exercise_frequency'),
            blurred_vision=data.get('blurred_vision', False),
            eye_pain=data.get('eye_pain', False),
            redness=data.get('redness', False),
            dry_eyes=data.get('dry_eyes', False),
            risk_level=data.get('risk_level'),
            risk_score=data.get('risk_score'),
            predicted_disease=data.get('predicted_disease'),
            confidence=data.get('confidence')
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        # Invalidate assessment stats cache
        invalidate_cache('assessment_stats')
        
        return jsonify({
            'message': 'Assessment created successfully',
            'assessment': assessment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/<string:assessment_id>', methods=['PUT'])
def update_assessment(assessment_id):
    try:
        assessment = Assessment.query.get_or_404(assessment_id)
        data = request.json
        
        # Note: reviewed, review_notes, reviewed_by columns don't exist in database
        # Skip these fields for now
        
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='View Assessment',
            entity_type='assessment',
            entity_id=assessment.id,
            details=f'Viewed assessment ID: {assessment.id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Assessment updated successfully',
            'assessment': assessment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/<string:assessment_id>', methods=['DELETE'])
def delete_assessment(assessment_id):
    try:
        assessment = Assessment.query.get_or_404(assessment_id)

        archive_entity(
            entity_type='assessment',
            entity_id=str(assessment_id),
            data=assessment.to_dict(),
            archived_by_admin_id=session.get('admin_id'),
            reason='Archived via admin delete endpoint',
        )

        db.session.delete(assessment)
        db.session.commit()

        invalidate_cache('assessment_stats')
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Archive Assessment',
            entity_type='assessment',
            entity_id=assessment_id,
            details=f'Archived assessment ID: {assessment_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Assessment archived successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/stats', methods=['GET'])
@cached(timeout=300, key_prefix='assessment_stats')  # Cache for 5 minutes
def get_assessment_stats():
    try:
        date_range = parse_request_date_range(default_days=30)

        base_filter = [
            Assessment.assessed_at >= date_range.start,
            Assessment.assessed_at < date_range.end_exclusive,
        ]

        total_assessments = Assessment.query.filter(*base_filter).count()
        high_risk = Assessment.query.filter(*base_filter, Assessment.risk_level == 'high').count()
        moderate_risk = Assessment.query.filter(*base_filter, Assessment.risk_level == 'moderate').count()
        low_risk = Assessment.query.filter(*base_filter, Assessment.risk_level == 'low').count()
        
        # Assessments today
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        assessments_today = Assessment.query.filter(Assessment.assessed_at >= today_start).count()
        
        # Calculate high risk growth (selected period vs previous period)
        previous_start = date_range.start - timedelta(days=date_range.days)
        previous_end = date_range.start

        current_period_high_risk = high_risk
        previous_period_high_risk = Assessment.query.filter(
            Assessment.risk_level == 'high',
            Assessment.assessed_at >= previous_start,
            Assessment.assessed_at < previous_end,
        ).count()
        
        if previous_period_high_risk > 0:
            high_risk_growth = round(((current_period_high_risk - previous_period_high_risk) / previous_period_high_risk) * 100, 1)
        else:
            high_risk_growth = 0.0
        
        # Assessments per day (selected date range)
        start_day = date_range.start.date()
        end_day = (date_range.end_exclusive - timedelta(microseconds=1)).date()

        rows = (
            db.session.query(
                func.date(Assessment.assessed_at).label('day'),
                func.count(Assessment.assessment_id).label('count'),
            )
            .filter(*base_filter)
            .group_by(func.date(Assessment.assessed_at))
            .all()
        )

        counts_by_day = {str(day): int(count) for day, count in rows}

        assessments_per_day = []
        current = start_day
        while current <= end_day:
            key = current.isoformat()
            assessments_per_day.append({'date': key, 'count': counts_by_day.get(key, 0)})
            current += timedelta(days=1)
        
        # Risk distribution
        risk_distribution = {
            'low': low_risk,
            'moderate': moderate_risk,
            'high': high_risk
        }
        
        return jsonify({
            'total_assessments': total_assessments,
            'high_risk': high_risk,
            'moderate_risk': moderate_risk,
            'low_risk': low_risk,
            'assessments_today': assessments_today,
            'high_risk_growth': high_risk_growth,
            'assessments_per_day': assessments_per_day,
            'risk_distribution': risk_distribution
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        if 'date' in error_msg or 'days' in error_msg:
            return jsonify({'error': error_msg}), 400
        return jsonify({'error': error_msg}), 500

@assessments_bp.route('/trends/risk-level', methods=['GET'])
@cached(timeout=600, key_prefix='assessment_risk_trend')  # Cache for 10 minutes
def get_risk_level_trends():
    """Get risk level trends over time (last 30 days)"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get assessments by risk level per day
        trends = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_start = datetime.combine(day.date(), datetime.min.time())
            day_end = day_start + timedelta(days=1)
            
            high = Assessment.query.filter(
                Assessment.risk_level == 'high',
                Assessment.assessed_at >= day_start,
                Assessment.assessed_at < day_end
            ).count()
            
            moderate = Assessment.query.filter(
                Assessment.risk_level == 'moderate',
                Assessment.assessed_at >= day_start,
                Assessment.assessed_at < day_end
            ).count()
            
            low = Assessment.query.filter(
                Assessment.risk_level == 'low',
                Assessment.assessed_at >= day_start,
                Assessment.assessed_at < day_end
            ).count()
            
            trends.append({
                'date': day.strftime('%Y-%m-%d'),
                'high': high,
                'moderate': moderate,
                'low': low,
                'total': high + moderate + low
            })
        
        return jsonify({
            'trends': trends,
            'period': f'last_{days}_days'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/analytics/disease-distribution', methods=['GET'])
@cached(timeout=600, key_prefix='disease_distribution')  # Cache for 10 minutes
def get_disease_distribution():
    """Get distribution of predicted diseases"""
    try:
        # Get disease counts
        disease_counts = db.session.query(
            Assessment.predicted_disease,
            func.count(Assessment.assessment_id).label('count')
        ).filter(
            Assessment.predicted_disease.isnot(None),
            Assessment.predicted_disease != ''
        ).group_by(
            Assessment.predicted_disease
        ).order_by(
            func.count(Assessment.assessment_id).desc()
        ).limit(10).all()
        
        distribution = [
            {'disease': disease, 'count': count}
            for disease, count in disease_counts
        ]
        
        return jsonify({
            'distribution': distribution,
            'total_diseases': len(disease_counts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/analytics/risk-factors', methods=['GET'])
@cached(timeout=600, key_prefix='risk_factors_analysis')  # Cache for 10 minutes
def analyze_risk_factors():
    """Analyze correlation between risk factors and risk levels"""
    try:
        # Get high-risk assessments
        high_risk = Assessment.query.filter_by(risk_level='high').all()
        total_high = len(high_risk)
        
        if total_high == 0:
            return jsonify({
                'message': 'No high-risk assessments found',
                'risk_factors': []
            }), 200
        
        # Count risk factors in high-risk assessments
        import json
        smoking_count = 0
        alcohol_count = 0
        high_screen_time = 0
        low_sleep = 0
        low_exercise = 0
        
        for assessment in high_risk:
            # Parse assessment data
            data = {}
            if assessment.assessment_data:
                try:
                    data = json.loads(assessment.assessment_data)
                except:
                    pass
            
            if data.get('smoking'):
                smoking_count += 1
            if data.get('alcohol'):
                alcohol_count += 1
            if data.get('screen_time_hours', 0) > 6:
                high_screen_time += 1
            if data.get('sleep_hours', 8) < 6:
                low_sleep += 1
            if data.get('physical_activity_level', 'moderate') == 'low':
                low_exercise += 1
        
        risk_factors = [
            {'factor': 'Smoking', 'percentage': round((smoking_count / total_high) * 100, 1)},
            {'factor': 'Alcohol Consumption', 'percentage': round((alcohol_count / total_high) * 100, 1)},
            {'factor': 'High Screen Time (>6hrs)', 'percentage': round((high_screen_time / total_high) * 100, 1)},
            {'factor': 'Low Sleep (<6hrs)', 'percentage': round((low_sleep / total_high) * 100, 1)},
            {'factor': 'Low Exercise', 'percentage': round((low_exercise / total_high) * 100, 1)}
        ]
        
        # Sort by percentage descending
        risk_factors.sort(key=lambda x: x['percentage'], reverse=True)
        
        return jsonify({
            'total_high_risk_assessments': total_high,
            'risk_factors': risk_factors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@assessments_bp.route('/export', methods=['GET'])
def export_assessments():
    """Export assessments with filtering support in CSV, JSON, or Excel format"""
    try:
        from flask import send_file
        from io import BytesIO
        from utils.export import export_to_csv, export_to_json, export_to_excel
        
        format_type = request.args.get('format', 'csv').lower()
        
        if format_type not in ['csv', 'json', 'excel']:
            return jsonify({'error': 'Invalid format. Use csv, json, or excel'}), 400
        
        # Build filtered query
        query = Assessment.query
        
        # Apply filters
        risk_level = request.args.get('risk_level', '').strip()
        if risk_level:
            query = query.filter(Assessment.risk_level == risk_level)
        
        user_id = request.args.get('user_id', '').strip()
        if user_id:
            query = query.filter(Assessment.user_id == user_id)
        
        start_date = request.args.get('start_date', '').strip()
        if start_date:
            query = query.filter(Assessment.assessed_at >= start_date)
        
        end_date = request.args.get('end_date', '').strip()
        if end_date:
            query = query.filter(Assessment.assessed_at <= end_date)
        
        # Get assessments
        assessments = query.order_by(Assessment.assessed_at.desc()).all()
        
        # Convert to dict
        assessments_data = [a.to_dict() for a in assessments]
        
        # Define columns for export
        columns = {
            'Assessment ID': 'id',
            'User Name': 'user_name',
            'Age': 'age',
            'BMI': 'bmi',
            'Blood Pressure': 'blood_pressure',
            'Blood Sugar': 'blood_sugar',
            'Smoking': 'smoking',
            'Alcohol': 'alcohol',
            'Screen Time (hrs)': 'screen_time',
            'Sleep Hours': 'sleep_hours',
            'Exercise Frequency': 'exercise_frequency',
            'Risk Level': 'risk_level',
            'Risk Score': 'risk_score',
            'Predicted Disease': 'predicted_disease',
            'Confidence': 'confidence',
            'Assessment Date': 'created_at'
        }
        
        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f'assessments_export_{timestamp}'
        
        # Export based on format
        if format_type == 'csv':
            file_content = export_to_csv(assessments_data, columns, filename)
            return send_file(
                BytesIO(file_content.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{filename}.csv'
            )
        elif format_type == 'json':
            file_content = export_to_json(assessments_data, filename)
            return send_file(
                BytesIO(file_content.encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'{filename}.json'
            )
        elif format_type == 'excel':
            file_content = export_to_excel(assessments_data, columns, filename)
            return send_file(
                file_content,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'{filename}.xlsx'
            )
        
        return jsonify({'error': 'Unsupported format'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
