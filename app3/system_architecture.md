# System Architecture for EyeCare

## Overview
The EyeCare system uses a client-server architecture with a mobile frontend and a backend for processing. It integrates a hybrid LightGBM and rule-based model for eye disease risk assessment.

## Architecture Layers

### 1. Presentation Layer (Mobile App)
- **Technology**: Flutter (Dart).
- **Components**: UI screens (e.g., login, profile input, assessment view).
- **Function**: Collects user data, displays results.
- **Files**: `app3/lib/screens/profile.dart`.

### 2. Application Layer (Backend)
- **Technology**: Flask (Python).
- **Components**: API routes for assessment, prediction, user management.
- **Function**: Handles requests, runs inference.
- **Files**: `eyecare_backend/app.py`, `routes/assessment.py`.

### 3. Data Layer
- **Technology**: MySQL.
- **Components**: Tables for users, health records, assessments.
- **Function**: Stores data securely.
- **Files**: `database.py`.

### 4. Model Layer
- **Technology**: LightGBM + custom rules.
- **Components**: Pre-trained model, rule engine.
- **Function**: Predicts risk, provides explanations.
- **Files**: `train_lightgbm.py`, `risk_score_calculator.py`.

## Architecture Chart (ASCII Art)

```
+-------------------+
|   Mobile App      |
|   (Flutter)       |
| - UI Screens      |
| - Data Input      |
+-------------------+
         |
         | HTTP/JSON
         v
+-------------------+
|   Backend         |
|   (Flask)         |
| - APIs            |
| - Inference       |
+-------------------+
         |
         | SQL
         v
+-------------------+
|   Database        |
|   (MySQL)         |
| - User Data       |
| - Assessments     |
+-------------------+
         |
         | Model Load
         v
+-------------------+
|   ML Model        |
|   (LightGBM + Rules)|
| - Prediction      |
| - Explanation     |
+-------------------+
```

## Explanation
The EyeCare system employs a layered client-server architecture to facilitate scalable and interpretable eye disease risk assessment. The presentation layer, implemented as a Flutter mobile application, serves as the user interface for data collection and result visualization, ensuring an intuitive experience with features like nullable input fields in profile screens. The application layer, built with Flask, manages API endpoints for user authentication, data submission, and inference requests, integrating the hybrid LightGBM and rule-based model for accurate predictions while maintaining operational safety. Data is persisted in a MySQL database layer, which stores user profiles, health records, and assessment results securely to support historical queries and compliance. At the core, the model layer combines LightGBM's gradient-boosting capabilities for capturing complex data patterns with custom rules for deterministic thresholds, enhanced by explainability tools like SHAP and LIME for transparency. Interactions between layers occur via secure HTTP/JSON communications and SQL queries, with the model loaded efficiently at startup. This architecture supports cross-platform deployment, containerization for scalability, and future extensions such as federated learning, as referenced in Ke et al. (2017) for LightGBM efficiency.

## References
Ke, G., et al. (2017). LightGBM. *Advances in Neural Information Processing Systems*, 30.
