from flask import Blueprint, request, jsonify
from services.db import get_connection
from services.email_service import mail
from flask_mail import Message
from datetime import datetime
from services.db import DB_DIALECT

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback and send confirmation email
    Expected JSON:
    {
        "user_id": "user123",
        "username": "John Doe",
        "email": "user@example.com",
        "rating": 5,
        "category": "Assessment Accuracy",
        "comment": "Great experience!"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'username', 'email', 'rating', 'category', 'comment']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        user_id = data['user_id']
        username = data['username']
        email = data['email']
        rating = data['rating']
        category = data['category']
        comment = data['comment']
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
        
        # Insert feedback into database
        submitted_at = datetime.now()

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                if DB_DIALECT == "postgres":
                    query = (
                        "INSERT INTO feedback (user_id, username, email, rating, category, comment, submitted_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING feedback_id"
                    )
                    cursor.execute(query, (user_id, username, email, rating, category, comment, submitted_at))
                    row = cursor.fetchone() or {}
                    feedback_id = row.get("feedback_id")
                else:
                    query = (
                        "INSERT INTO feedback (user_id, username, email, rating, category, comment, submitted_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    )
                    cursor.execute(query, (user_id, username, email, rating, category, comment, submitted_at))
                    feedback_id = getattr(cursor, "lastrowid", None)

            conn.commit()
        finally:
            conn.close()
        
        # Send confirmation email
        try:
            send_feedback_confirmation_email(email, username, rating, category, comment)
        except Exception as email_error:
            print(f"Failed to send confirmation email: {email_error}")
            # Don't fail the request if email fails
        
        return jsonify({
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id,
            "submitted_at": submitted_at.isoformat()
        }), 201
        
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return jsonify({"error": "Failed to submit feedback"}), 500


@feedback_bp.route('/feedback/user/<user_id>', methods=['GET'])
def get_user_feedback(user_id):
    """Get all feedback submitted by a specific user"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                query = (
                    "SELECT feedback_id, rating, category, comment, submitted_at "
                    "FROM feedback WHERE user_id = %s ORDER BY submitted_at DESC"
                )
                cursor.execute(query, (user_id,))
                feedback_list = cursor.fetchall()
        finally:
            conn.close()
        
        # Format dates
        for feedback in feedback_list:
            if feedback['submitted_at']:
                feedback['submitted_at'] = feedback['submitted_at'].isoformat()
        
        return jsonify({
            "status": "success",
            "feedback": feedback_list,
            "count": len(feedback_list)
        }), 200
        
    except Exception as e:
        print(f"Error fetching feedback: {e}")
        return jsonify({"error": "Failed to fetch feedback"}), 500


def send_feedback_confirmation_email(to_email, username, rating, category, comment):
    """Send confirmation email after feedback submission"""
    
    # Rating emoji map
    rating_emojis = {
        1: "😞 Poor",
        2: "😕 Fair",
        3: "🙂 Good",
        4: "😊 Very Good",
        5: "🤩 Excellent"
    }
    
    rating_text = rating_emojis.get(rating, f"{rating} stars")
    
    subject = "Thank You for Your Feedback - EyeCare"
    
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #673AB7 0%, #42A5F5 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">Thank You for Your Feedback!</h1>
                </div>
                
                <div style="padding: 30px; background-color: #f9f9f9;">
                    <p style="font-size: 16px;">Dear <strong>{username}</strong>,</p>
                    
                    <p>Thank you for taking the time to share your feedback with us. Your input is invaluable in helping us improve EyeCare and provide better eye health assessment services.</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #673AB7;">
                        <h3 style="margin-top: 0; color: #673AB7;">Your Feedback Summary</h3>
                        <p><strong>Rating:</strong> {rating_text}</p>
                        <p><strong>Category:</strong> {category}</p>
                        <p><strong>Comment:</strong></p>
                        <p style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; font-style: italic;">"{comment}"</p>
                    </div>
                    
                    <p>Our team carefully reviews all feedback to continuously enhance our AI-powered risk assessment model and improve user experience.</p>
                    
                    <p>If you have any urgent concerns or need assistance, please don't hesitate to contact us.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                        <p style="margin: 0;">Best regards,</p>
                        <p style="margin: 5px 0; font-weight: bold; color: #673AB7;">The EyeCare Team</p>
                    </div>
                </div>
                
                <div style="padding: 20px; text-align: center; background-color: #f0f0f0; border-radius: 0 0 10px 10px;">
                    <p style="font-size: 12px; color: #666; margin: 0;">This is an automated message from EyeCare. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    msg = Message(
        subject=subject,
        recipients=[to_email],
        html=body
    )
    
    mail.send(msg)
