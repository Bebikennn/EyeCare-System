# EyeCare Database Schema Documentation

**Database:** eyecare_db  
**MySQL Version:** MariaDB 10.4.32  
**Charset:** utf8mb4_unicode_ci

## Table of Contents
1. [Users & Authentication](#users--authentication)
2. [Health Data](#health-data)
3. [Assessments & Predictions](#assessments--predictions)
4. [Admin & Activity](#admin--activity)
5. [Machine Learning](#machine-learning)
6. [Views](#views)

---

## Users & Authentication

### users
User account information for the mobile app
```sql
user_id             VARCHAR(36) PRIMARY KEY    -- UUID
username            VARCHAR(100) UNIQUE NOT NULL
email               VARCHAR(255) UNIQUE NOT NULL
password_hash       VARCHAR(255)
full_name           VARCHAR(255)
phone_number        VARCHAR(20)
address             TEXT
profile_picture     LONGBLOB                   -- Binary image data
profile_picture_url VARCHAR(500)
created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at          TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
status              VARCHAR(20) DEFAULT 'active'  -- 'active', 'blocked', 'archived'
```

**Note:** Age and gender are NOT in this table - they're in `health_records`

### user_notifications
Push notifications for mobile app users
```sql
notification_id     VARCHAR(36) PRIMARY KEY    -- UUID
user_id             VARCHAR(36) FK -> users.user_id
title               VARCHAR(255) NOT NULL
message             TEXT NOT NULL
type                ENUM('info','success','warning','error') DEFAULT 'info'
is_read             TINYINT(1) DEFAULT 0
link                VARCHAR(255)               -- Deep link URL
created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## Health Data

### health_records
Medical history and biometric data
```sql
record_id               VARCHAR(36) PRIMARY KEY
user_id                 VARCHAR(36) FK -> users.user_id
age                     INT(11)
gender                  ENUM('Male','Female','Other')
bmi                     DECIMAL(5,2)
medical_history         TEXT
blood_pressure          VARCHAR(20)            -- e.g., "120/80"
blood_sugar             VARCHAR(20)            -- e.g., "95 mg/dL"
diabetes                TINYINT(1) DEFAULT 0   -- Boolean
hypertension            TINYINT(1) DEFAULT 0
previous_eye_surgery    TINYINT(1) DEFAULT 0
date_recorded           DATE NOT NULL
```

### habit_data
Lifestyle and daily habits tracking
```sql
habit_id                    VARCHAR(36) PRIMARY KEY
user_id                     VARCHAR(36) FK -> users.user_id
screen_time_hours           DECIMAL(4,2)
sleep_hours                 DECIMAL(4,2)
diet_quality                INT(11)                -- Score 1-10
smoking_status              ENUM('Yes','No','Former')
alcohol_use                 TINYINT(1)
outdoor_activity_hours      DECIMAL(4,2)
water_intake_liters         DECIMAL(4,2)
physical_activity_level     ENUM('Low','Moderate','High')
glasses_usage               TINYINT(1)
recorded_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### eye_symptoms
Eye-specific symptoms and family history
```sql
symptom_id                  VARCHAR(36) PRIMARY KEY
user_id                     VARCHAR(36) FK -> users.user_id
eye_pain_frequency          INT(11)                -- Scale 0-10
blurry_vision_score         INT(11)                -- Scale 0-10
light_sensitivity           ENUM('Yes','No')
eye_strains_per_day         INT(11)
family_history_eye_disease  TINYINT(1)
recorded_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## Assessments & Predictions

### assessment_results
ML model predictions and risk assessments
```sql
assessment_id       VARCHAR(36) PRIMARY KEY    -- UUID
user_id             VARCHAR(36) FK -> users.user_id
risk_level          ENUM('Low','Moderate','High','Critical')
risk_score          DECIMAL(5,2)               -- 0-100
confidence_score    DECIMAL(5,2)               -- Model confidence
predicted_disease   VARCHAR(100)
model_version       VARCHAR(50)                -- e.g., "LightGBM-20251209-230503"
assessment_data     LONGTEXT (JSON)            -- Full input features
per_disease_scores  LONGTEXT (JSON)            -- Probability for each disease
assessed_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Disease Classes:**
- Astigmatism
- Blurred Vision
- Dry Eye
- Hyperopia
- Light Sensitivity
- Myopia
- Presbyopia

**Note:** No 'reviewed', 'review_notes', or 'reviewed_by' columns exist

### recommendations
AI-generated health recommendations
```sql
recommendation_id   VARCHAR(36) PRIMARY KEY
assessment_id       VARCHAR(36) FK -> assessment_results.assessment_id
recommendation_text TEXT NOT NULL
priority            ENUM('High','Medium','Low') DEFAULT 'Medium'
category            VARCHAR(100)               -- 'Lifestyle', 'Medical', 'Prevention'
created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### health_tips
Static health tips content
```sql
tip_id              INT(11) AUTO_INCREMENT PRIMARY KEY
title               VARCHAR(255) NOT NULL
description         TEXT NOT NULL
category            VARCHAR(100)               -- 'Screen Time', 'Sleep', 'Nutrition'
icon                VARCHAR(50)                -- Material icon name
risk_level          ENUM('Low','Moderate','High','All') DEFAULT 'All'
created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### feedback
User feedback on assessments/recommendations
```sql
feedback_id         INT(11) AUTO_INCREMENT PRIMARY KEY
user_id             VARCHAR(36) FK -> users.user_id
feedback_type       VARCHAR(50)
rating              INT(11)                    -- 1-5 stars
comment             TEXT
submitted_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## Admin & Activity

### admins
Admin panel user accounts
```sql
id                          INT(11) AUTO_INCREMENT PRIMARY KEY
username                    VARCHAR(50) UNIQUE NOT NULL
email                       VARCHAR(100) UNIQUE NOT NULL
password_hash               VARCHAR(255) NOT NULL
full_name                   VARCHAR(100) NOT NULL
role                        ENUM('super_admin','admin','data_analyst','analyst','staff')
status                      ENUM('active','inactive')
must_change_password        TINYINT(1) DEFAULT 0
profile_picture             VARCHAR(255)
last_login                  TIMESTAMP
created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
email_verified              TINYINT(1) DEFAULT 0
email_verified_at           TIMESTAMP NULL
email_verification_token    VARCHAR(100)
email_verification_expires  TIMESTAMP NULL
reset_token                 VARCHAR(100)
reset_token_expires         TIMESTAMP NULL
```

**Role Permissions:**
- `super_admin`: Full access, can make changes directly
- `admin`: Most actions, can make changes directly
- `data_analyst`: Read-only + some actions via approvals
- `analyst`: Read-only
- `staff`: Limited read access

### activity_logs
Audit trail of admin actions
```sql
id              INT(11) AUTO_INCREMENT PRIMARY KEY
admin_id        INT(11) FK -> admins.id
action          VARCHAR(100) NOT NULL          -- 'Create User', 'Update Admin', etc.
entity_type     VARCHAR(50)                    -- 'user', 'admin', 'assessment'
entity_id       VARCHAR(100)
details         TEXT                           -- JSON or plain text description
ip_address      VARCHAR(45)
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Stored Procedures:**
- `get_recent_activity(admin_id, limit)` - Get recent actions by admin
- `log_admin_activity(...)` - Insert activity log entry

### admin_notifications
Notifications for admin panel users
```sql
id              INT(11) AUTO_INCREMENT PRIMARY KEY
admin_id        INT(11) FK -> admins.id
title           VARCHAR(255) NOT NULL
message         TEXT NOT NULL
type            ENUM('info','success','warning','error','approval') DEFAULT 'info'
is_read         TINYINT(1) DEFAULT 0
link            VARCHAR(255)
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### admin_settings
System-wide configuration
```sql
id              INT(11) AUTO_INCREMENT PRIMARY KEY
setting_key     VARCHAR(100) UNIQUE NOT NULL
setting_value   TEXT
description     TEXT
updated_by      INT(11) FK -> admins.id
updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Default Settings:**
- `approval_required_for_staff`: 'true'
- `approval_required_for_data_analyst`: 'true'
- `max_login_attempts`: '5'
- `session_timeout_minutes`: '30'
- `maintenance_mode`: 'false'
- `backup_frequency_hours`: '24'
- `email_notifications_enabled`: 'true'
- `data_retention_days`: '365'

### pending_actions
Approval workflow for non-privileged admins
```sql
id              INT(11) AUTO_INCREMENT PRIMARY KEY
action_type     VARCHAR(50) NOT NULL           -- 'create', 'update', 'delete'
entity_type     VARCHAR(50) NOT NULL           -- 'user', 'admin', 'health_tip'
entity_id       VARCHAR(100)
entity_data     TEXT                           -- JSON of changes
status          VARCHAR(20)                    -- 'pending', 'approved', 'rejected'
requested_by    INT(11) FK -> admins.id
approved_by     INT(11) FK -> admins.id
reason          TEXT
created_at      DATETIME
updated_at      DATETIME
```

**Note:** No `super_admin_reviewed_at` column exists

---

## Machine Learning

### ml_metrics
Training metrics and model performance
```sql
id                  INT(11) AUTO_INCREMENT PRIMARY KEY
model_version       VARCHAR(50) NOT NULL       -- e.g., "LightGBM-20251209-230503"
accuracy            DECIMAL(5,4)               -- e.g., 1.0000
precision           DECIMAL(5,4)
recall              DECIMAL(5,4)
f1_score            DECIMAL(5,4)
confusion_matrix    TEXT (JSON)                -- 10x10 matrix
feature_importance  TEXT (JSON)                -- Feature name: score
training_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
dataset_size        INT(11)                    -- e.g., 15000
notes               TEXT (JSON)                -- Full training details
```

**Current Model Performance (LightGBM-20251209-230503):**
- Accuracy: 100%
- Precision: 100%
- Recall: 100%
- F1-Score: 100%
- Dataset: 15,000 samples (12,000 train, 3,000 test)

**Top Feature Importance:**
1. Age: 4346.0
2. Eye_Strains_Per_Day: 2847.0
3. Light_Sensitivity: 2395.0
4. Blurry_Vision_Score: 2234.0
5. Eye_Pain_Frequency: 1806.0

---

## Views

### user_profile_view
Comprehensive user profile with latest health data
```sql
-- Combines data from:
-- users + health_records (latest) + habit_data (latest) + eye_symptoms (latest) + assessment_results (latest)

SELECT
    u.user_id, u.username, u.full_name, u.email, u.phone_number, u.address,
    hr.age, hr.gender, hr.bmi, hr.diabetes, hr.hypertension, hr.previous_eye_surgery,
    hd.screen_time_hours, hd.sleep_hours, hd.diet_quality, hd.smoking_status,
    hd.alcohol_use, hd.outdoor_activity_hours, hd.water_intake_liters,
    hd.physical_activity_level, hd.glasses_usage,
    es.eye_pain_frequency, es.blurry_vision_score, es.light_sensitivity,
    es.eye_strains_per_day, es.family_history_eye_disease,
    ar.risk_level AS latest_risk_level,
    ar.risk_score AS latest_risk_score,
    ar.predicted_disease AS latest_predicted_disease,
    ar.assessed_at AS last_assessment_date
FROM users u
LEFT JOIN (latest health_records) hr ON u.user_id = hr.user_id
LEFT JOIN (latest habit_data) hd ON u.user_id = hd.user_id
LEFT JOIN (latest eye_symptoms) es ON u.user_id = es.user_id
LEFT JOIN (latest assessment_results) ar ON u.user_id = ar.user_id
```

### admin_activity_summary
Admin statistics and last activity
```sql
SELECT
    a.id AS admin_id,
    a.username,
    a.full_name,
    a.role,
    COUNT(al.id) AS total_actions,
    MAX(al.created_at) AS last_activity,
    a.last_login
FROM admins a
LEFT JOIN activity_logs al ON a.id = al.admin_id
GROUP BY a.id, a.username, a.full_name, a.role, a.last_login
```

### ml_metrics_summary
Ranked ML models by accuracy and recency
```sql
SELECT
    model_version,
    accuracy,
    precision,
    recall,
    f1_score,
    dataset_size,
    training_date,
    RANK() OVER (ORDER BY accuracy DESC) AS accuracy_rank,
    RANK() OVER (ORDER BY training_date DESC) AS recency_rank
FROM ml_metrics
ORDER BY training_date DESC
```

---

## Key Relationships

```
users (1) --> (N) assessment_results
users (1) --> (N) health_records
users (1) --> (N) habit_data
users (1) --> (N) eye_symptoms
users (1) --> (N) feedback
users (1) --> (N) user_notifications

assessment_results (1) --> (N) recommendations

admins (1) --> (N) activity_logs
admins (1) --> (N) admin_notifications
admins (1) --> (N) pending_actions (as requester)
admins (1) --> (N) pending_actions (as approver)
admins (1) --> (N) admin_settings (as updater)
```

---

## Data Samples

### Current Database Stats (as of import):
- **Users:** 7 (6 active, 1 archived)
- **Admins:** 6 (admin, analyst, staff, admin john, manager)
- **Assessment Results:** 4 (all for user John)
- **Health Records:** 11 (mostly for user John)
- **Health Tips:** 10 (default tips)
- **ML Metrics:** 2 training runs (both 100% accuracy)

---

## Important Notes

### Fields That DON'T Exist:
❌ `users.age` - Use `health_records.age` instead  
❌ `users.gender` - Use `health_records.gender` instead  
❌ `users.first_name`, `users.last_name` - Use `users.full_name` instead  
❌ `assessment_results.reviewed` - No review columns exist  
❌ `assessment_results.review_notes` - No review columns exist  
❌ `assessment_results.reviewed_by` - No review columns exist  
❌ `pending_actions.requester_id` - Use `requested_by` instead  
❌ `pending_actions.super_admin_reviewed_at` - Doesn't exist  

### Fields That DO Exist:
✅ `users.status` - Values: 'active', 'blocked', 'archived'  
✅ `admins.must_change_password` - Force password change on next login  
✅ `pending_actions.requested_by` - Admin who submitted the request  

---

## Generated: 2025-12-XX
**Source:** eyecare_db (3).sql from phpMyAdmin export
