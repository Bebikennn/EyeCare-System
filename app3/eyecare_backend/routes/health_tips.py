from flask import Blueprint, jsonify
from services.db import get_connection

health_tips_bp = Blueprint("health_tips", __name__, url_prefix='/api/health-tips')

# Default health tips categories
DEFAULT_TIPS = [
    {
        'title': 'Healthy Vision Lifestyle',
        'emoji': '👁️',
        'color': '0xFF4CAF50',
        'tips': [
            'Follow the 20-20-20 rule to reduce eye fatigue.',
            'Maintain good lighting and posture during screen work.',
            'Limit continuous screen time. Take frequent short breaks.',
        ],
    },
    {
        'title': 'Nutrition for Eye Health',
        'emoji': '🥗',
        'color': '0xFF009688',
        'tips': [
            'Include leafy greens and foods rich in omega-3.',
            'Hydrate to reduce dry eye symptoms.',
            'Limit processed sugars and refined carbs.',
        ],
    },
    {
        'title': 'Lifestyle & Daily Habits',
        'emoji': '🏃',
        'color': '0xFF2196F3',
        'tips': [
            'Exercise regularly to improve circulation.',
            'Quit smoking to reduce vascular damage.',
            'Target healthy sleep and maintain a stable schedule.',
        ],
    },
    {
        'title': 'Environmental Protection',
        'emoji': '🕶️',
        'color': '0xFFFF9800',
        'tips': [
            'Use UV-protective sunglasses outdoors.',
            'Use humidifiers in dry environments.',
            'Reduce exposure to dust and pollutants.',
        ],
    },
]


@health_tips_bp.route('/user/<user_id>', methods=['GET'])
def get_health_tips(user_id):
    """Get health tips and user's risk score"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Get user's latest assessment to calculate risk score
            cur.execute("""
                SELECT 
                    risk_score,
                    risk_level
                FROM assessment_results
                WHERE user_id = %s
                ORDER BY assessed_at DESC
                LIMIT 1
            """, (user_id,))
            
            result = cur.fetchone()
            if result:
                risk_score = float(result.get('risk_score', 0.0))
                risk_level = result.get('risk_level', 'Unknown')
            else:
                risk_score = 0.0
                risk_level = 'No Assessment'

        return jsonify({
            'status': 'success',
            'tips': DEFAULT_TIPS,
            'risk_score': risk_score,
            'risk_level': risk_level,
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
        }), 500
    finally:
        if conn:
            conn.close()


@health_tips_bp.route('/user/<user_id>/personalized', methods=['GET'])
def get_personalized_tips(user_id):
    """Get personalized health tips based on user's assessment data"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Get user's latest assessment
            cur.execute("""
                SELECT 
                    risk_score,
                    risk_level
                FROM assessment_results
                WHERE user_id = %s
                ORDER BY assessed_at DESC
                LIMIT 1
            """, (user_id,))
            
            assessment = cur.fetchone()
            
            if not assessment:
                risk_score = 0.0
                risk_level = 'No Assessment'
            else:
                risk_score = float(assessment.get('risk_score', 0.0))
                risk_level = assessment.get('risk_level', 'Unknown')

            # Return default tips with user's risk score
            # In a real application, you would customize tips based on assessment_data
            return jsonify({
                'status': 'success',
                'tips': DEFAULT_TIPS,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'personalized': True,
            }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
        }), 500
    finally:
        if conn:
            conn.close()


@health_tips_bp.route('/categories', methods=['GET'])
def get_all_categories():
    """Get all health tip categories (no user authentication needed)"""
    try:
        return jsonify({
            'status': 'success',
            'tips': DEFAULT_TIPS,
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
        }), 500
