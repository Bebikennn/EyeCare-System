"""
Database Models Mapping for MySQL (eyecare_db)
Maps existing MySQL tables to SQLAlchemy models
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ===========================================
# EXISTING MYSQL TABLES (from app3)
# ===========================================

class User(db.Model):
    """Maps to 'users' table in MySQL"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    user_id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    full_name = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.user_id,
            'full_name': self.full_name or self.username,
            'email': self.email,
            'phone': self.phone_number,
            'status': self.status or 'active',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': None,
            'total_assessments': len(self.assessments) if self.assessments else 0
        }

class Assessment(db.Model):
    """Maps to 'assessment_results' table in MySQL"""
    __tablename__ = 'assessment_results'
    __table_args__ = {'extend_existing': True}
    
    assessment_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float)
    predicted_disease = db.Column(db.String(100))
    model_version = db.Column(db.String(50), default='LightGBM_v1.0')
    assessment_data = db.Column(db.Text)  # JSON string
    per_disease_scores = db.Column(db.Text)  # JSON string
    assessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def id(self):
        """Alias for compatibility with admin dashboard"""
        return self.assessment_id
    
    @property
    def created_at(self):
        """Alias for compatibility"""
        return self.assessed_at
    
    def to_dict(self):
        import json
        
        # Parse assessment_data JSON if available
        assessment_json = {}
        if self.assessment_data:
            try:
                assessment_json = json.loads(self.assessment_data)
            except:
                pass
        
        return {
            'id': self.assessment_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'N/A',
            'age': assessment_json.get('age'),
            'bmi': assessment_json.get('bmi'),
            'blood_pressure': assessment_json.get('blood_pressure'),
            'blood_sugar': assessment_json.get('blood_sugar'),
            'smoking': assessment_json.get('smoking', False),
            'alcohol': assessment_json.get('alcohol', False),
            'screen_time': assessment_json.get('screen_time_hours'),
            'sleep_hours': assessment_json.get('sleep_hours'),
            'exercise_frequency': assessment_json.get('physical_activity_level'),
            'blurred_vision': assessment_json.get('blurred_vision', False),
            'eye_pain': assessment_json.get('eye_pain', False),
            'redness': assessment_json.get('redness', False),
            'dry_eyes': assessment_json.get('dry_eyes', False),
            'risk_level': self.risk_level.lower() if self.risk_level else 'low',
            'risk_score': self.risk_score,
            'predicted_disease': self.predicted_disease,
            'confidence': self.confidence_score,
            'model_version': self.model_version,
            'created_at': self.assessed_at.isoformat() if self.assessed_at else None
        }

class HealthTip(db.Model):
    """Maps to 'health_tips' table in MySQL"""
    __tablename__ = 'health_tips'
    __table_args__ = {'extend_existing': True}
    
    tip_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    icon = db.Column(db.String(50))
    risk_level = db.Column(db.String(20), default='All')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def id(self):
        """Alias for compatibility"""
        return self.tip_id
    
    @property
    def content(self):
        """Alias for compatibility"""
        return self.description
    
    @property
    def image_url(self):
        """Alias for compatibility"""
        return None
    
    @property
    def status(self):
        """Alias for compatibility"""
        return 'active'
    
    @property
    def updated_at(self):
        """Alias for compatibility"""
        return self.created_at
    
    def to_dict(self):
        return {
            'id': self.tip_id,
            'title': self.title,
            'content': self.description,
            'category': self.category,
            'image_url': None,
            'status': 'active',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.created_at.isoformat() if self.created_at else None
        }

# ===========================================
# NEW ADMIN TABLES (will be created)
# ===========================================

class Admin(db.Model):
    """Admin accounts for dashboard"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='staff')  # super_admin, analyst, staff
    status = db.Column(db.String(20), default='active')
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Unmapped fields used for password reset flow (no DB migration required)
    reset_token = None
    reset_token_expiry = None
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expires_in_seconds: int = 3600):
        """Generate a signed reset token.

        Stores token+expiry on the instance for UI/tests, but verification is
        signature-based and does not require DB columns.
        """
        from datetime import timedelta
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps({'admin_id': self.id}, salt='admin-reset')
        self.reset_token = token
        self.reset_token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        return token

    def verify_reset_token(self, token: str, max_age_seconds: int = 3600) -> bool:
        """Verify token signature and expiry."""
        try:
            if self.reset_token_expiry and self.reset_token_expiry < datetime.now(timezone.utc):
                return False

            from flask import current_app
            from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            data = serializer.loads(token, salt='admin-reset', max_age=max_age_seconds)
            return str(data.get('admin_id')) == str(self.id)
        except (BadSignature, SignatureExpired, Exception):
            return False

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None

    @classmethod
    def get_by_reset_token(cls, token: str, max_age_seconds: int = 3600):
        """Resolve an Admin from a signed reset token."""
        try:
            from flask import current_app
            from itsdangerous import URLSafeTimedSerializer

            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            data = serializer.loads(token, salt='admin-reset', max_age=max_age_seconds)
            admin_id = data.get('admin_id')
            if not admin_id:
                return None
            return cls.query.get(int(admin_id))
        except Exception:
            return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class AdminPasswordResetOTP(db.Model):
    """One-time password records for admin forgot-password flow."""
    __tablename__ = 'admin_password_reset_otps'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False, index=True)
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    consumed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    consumed_at = db.Column(db.DateTime)

    admin = db.relationship('Admin', backref=db.backref('password_reset_otps', lazy=True))

class ActivityLog(db.Model):
    """Activity logs for admin actions"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.String(100))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('Admin', backref='activity_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_name': self.admin.full_name if self.admin else 'System',
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MLMetrics(db.Model):
    """ML model performance metrics"""
    __tablename__ = 'ml_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(50), nullable=False)
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    confusion_matrix = db.Column(db.Text)  # JSON string
    feature_importance = db.Column(db.Text)  # JSON string
    training_date = db.Column(db.DateTime, default=datetime.utcnow)
    dataset_size = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_version': self.model_version,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'confusion_matrix': self.confusion_matrix,
            'feature_importance': self.feature_importance,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'dataset_size': self.dataset_size
        }

class AdminNotification(db.Model):
    """Notifications for admin dashboard"""
    __tablename__ = 'admin_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, warning, error, success
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('Admin', backref=db.backref('notifications', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ArchivedEntity(db.Model):
    """Archived snapshots for delete operations.

    This avoids changing legacy MySQL tables (users/assessment_results/health_tips)
    while still providing a 30-day retention window.
    """

    __tablename__ = 'archived_entities'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(100), nullable=False)
    data_json = db.Column(db.Text, nullable=False)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    archived_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    purge_after_days = db.Column(db.Integer, default=30, nullable=False)
    reason = db.Column(db.Text)

    archived_by = db.relationship('Admin', backref=db.backref('archives', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'archived_by_admin_id': self.archived_by_admin_id,
            'purge_after_days': self.purge_after_days,
            'reason': self.reason,
        }

class PendingAction(db.Model):
    """Pending actions that require approval"""
    __tablename__ = 'pending_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False)  # create_user, update_settings, delete_data
    entity_type = db.Column(db.String(50), nullable=False)  # user, healthtip, system
    entity_id = db.Column(db.String(100))
    entity_data = db.Column(db.Text)  # JSON data
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    requested_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requester = db.relationship('Admin', foreign_keys=[requested_by], backref=db.backref('requested_actions', lazy=True))
    approver = db.relationship('Admin', foreign_keys=[approved_by], backref=db.backref('approved_actions', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'entity_data': self.entity_data,
            'status': self.status,
            'requested_by': self.requested_by,
            'approved_by': self.approved_by,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

def init_db():
    """Initialize database with admin tables and default data"""
    import os
    db.create_all()
    
    # Create default super admin if not exists
    if not Admin.query.filter_by(username='admin').first():
        is_production = (os.getenv('FLASK_ENV', '').lower() == 'production') or bool(os.getenv('RENDER'))

        username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@eyecare.com')
        full_name = os.getenv('DEFAULT_ADMIN_FULL_NAME', 'Super Administrator')

        password = os.getenv('DEFAULT_ADMIN_PASSWORD')
        if is_production and not password:
            # In production, do not create an account with a known default password.
            print(
                "DEFAULT_ADMIN_PASSWORD not set; skipping default admin creation. "
                "Create an admin user manually or set DEFAULT_ADMIN_PASSWORD and re-run init."
            )
            return

        # Non-production fallback for local/dev convenience.
        if not password:
            password = 'admin123'

        admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            role='super_admin',
            status='active'
        )
        admin.set_password(password)
        db.session.add(admin)
        
        # Add sample ML metrics
        metrics = MLMetrics(
            model_version='LightGBM-v1.0',
            accuracy=0.9245,
            precision=0.9156,
            recall=0.9087,
            f1_score=0.9121,
            confusion_matrix='[[45, 3], [4, 48]]',
            feature_importance='{"age": 0.25, "bmi": 0.18, "screen_time": 0.15, "blood_sugar": 0.12, "smoking": 0.10, "blood_pressure": 0.08, "exercise_frequency": 0.07, "sleep_hours": 0.05}',
            dataset_size=1250
        )
        db.session.add(metrics)
        
        db.session.commit()
        print("Database initialized with default admin account")
        if not is_production:
            print("Username: admin, Password: admin123")

def get_db_connection():
    """Get database connection using DB_CONFIG"""
    import os
    from config import DB_CONFIG

    database_url = (os.getenv('DATABASE_URL') or '').strip()
    if database_url.lower().startswith(('postgres://', 'postgresql://')):
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        import psycopg2
        from psycopg2.extras import RealDictCursor

        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

    import pymysql
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor,
    )

def get_app_db_connection():
    """Alias for get_db_connection for backward compatibility"""
    return get_db_connection()
