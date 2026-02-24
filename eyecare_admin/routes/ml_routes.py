from flask import Blueprint, request, jsonify, session
from database import db, MLMetrics, ActivityLog, get_app_db_connection
import json
import os
import pickle
import sys

# Add parent directory to path for risk score calculator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from risk_score_calculator import calculate_risk_score, get_risk_level

try:
    from ml_risk_predict import predict_risk_two_stage
except Exception:
    predict_risk_two_stage = None

ml_bp = Blueprint('ml', __name__)

@ml_bp.route('/predict', methods=['POST'])
def predict_assessment():
    """Real-time prediction using trained LightGBM model"""
    try:
        data = request.json

        # Prefer the new two-stage risk model if available.
        if predict_risk_two_stage is not None:
            try:
                result = predict_risk_two_stage(data or {})

                # Use latest model version from database if available.
                latest_metrics = MLMetrics.query.order_by(MLMetrics.training_date.desc()).first()
                model_version = latest_metrics.model_version if latest_metrics else "RiskModel-Unknown"
                result["model_version"] = model_version

                return jsonify(result), 200
            except FileNotFoundError:
                # Risk model not trained yet; fall back to legacy behavior below.
                pass
            except Exception:
                # If anything unexpected happens, fall back to legacy behavior below.
                pass
        
        # Calculate risk score using Excel formula
        risk_score = calculate_risk_score(data)
        risk_level_from_score = get_risk_level(risk_score)
        
        # Load the actual trained model
        model_path = 'models/eyecare_lightgbm_model.pkl'
        
        if not os.path.exists(model_path):
            return jsonify({
                'error': 'Model not found. Please train the model first using train_lightgbm.py'
            }), 404
        
        # Load model
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
            model = model_data['model']
            label_encoder = model_data['label_encoder']
            feature_names = model_data['feature_names']
        
        # Prepare input features in the correct order
        import pandas as pd
        input_features = {}
        
        # Map input data to model features
        for feature in feature_names:
            if feature == 'Gender_Male':
                input_features[feature] = 1 if data.get('gender', '').lower() == 'male' else 0
            elif feature == 'Risk Score':
                # Use calculated risk score from Excel formula
                input_features[feature] = risk_score if risk_score is not None else 0
            else:
                # Convert feature name to match input data format
                feature_key = feature.lower().replace(' ', '_')
                input_features[feature] = data.get(feature_key, 0)
        
        # Create DataFrame with features in correct order
        X = pd.DataFrame([input_features], columns=feature_names)
        
        # Make prediction
        prediction = model.predict(X)[0]
        prediction_proba = model.predict_proba(X)[0]
        
        # Decode prediction
        predicted_disease = label_encoder.inverse_transform([prediction])[0]
        confidence = float(prediction_proba[prediction])
        
        # Keratitis is out of scope; never surface it in API responses
        if predicted_disease == 'Keratitis':
            predicted_disease = 'Other / Unspecified'

        # Calculate risk level based on disease and risk score
        high_risk_diseases = []
        moderate_risk_diseases = ['Dry Eye', 'Light Sensitivity']
        
        if predicted_disease in high_risk_diseases:
            risk_level = 'High'
        elif predicted_disease in moderate_risk_diseases:
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
        
        # Get latest model version from database
        latest_metrics = MLMetrics.query.order_by(MLMetrics.training_date.desc()).first()
        model_version = latest_metrics.model_version if latest_metrics else 'LightGBM-Unknown'
        
        result = {
            'risk_level': risk_level,
            'risk_score': risk_score if risk_score is not None else 0,
            'predicted_disease': predicted_disease,
            'confidence': confidence,
            'model_version': model_version,
            'risk_score_breakdown': {
                'calculated_score': risk_score,
                'risk_level_from_formula': risk_level_from_score,
                'predicted_risk_level': risk_level
            },
            'all_predictions': {
                label_encoder.inverse_transform([i])[0]: float(prob)
                for i, prob in enumerate(prediction_proba)
                if label_encoder.inverse_transform([i])[0] != 'Keratitis'
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@ml_bp.route('/metrics', methods=['GET'])
def get_metrics():
    try:
        # Get the latest metrics (should be from train_lightgbm.py)
        metrics = MLMetrics.query.order_by(MLMetrics.training_date.desc()).first()
        
        if not metrics:
            return jsonify({'error': 'No metrics found. Run train_lightgbm.py to train the model.'}), 404
        
        metrics_dict = metrics.to_dict()

        # Parse feature importance
        try:
            feature_importance = json.loads(metrics_dict.get('feature_importance', '{}'))
        except Exception:
            feature_importance = {}
        
        # Parse confusion matrix
        try:
            confusion_matrix = json.loads(metrics_dict.get('confusion_matrix', '[]'))
        except Exception:
            confusion_matrix = []
        
        # Parse notes for additional info
        try:
            notes = json.loads(metrics_dict.get('notes', '{}'))
        except Exception:
            notes = {}
        
        # Return comprehensive metrics
        response = {
            'metrics': {
                'id': metrics_dict['id'],
                'model_version': metrics_dict['model_version'],
                'accuracy': metrics_dict['accuracy'],
                'precision': metrics_dict['precision'],
                'recall': metrics_dict['recall'],
                'f1_score': metrics_dict['f1_score'],
                'dataset_size': metrics_dict['dataset_size'],
                'training_date': metrics_dict['training_date'],
                'feature_importance': feature_importance,
                'confusion_matrix': confusion_matrix,
                'notes': notes
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/metrics/history', methods=['GET'])
def get_metrics_history():
    try:
        metrics_list = MLMetrics.query.order_by(MLMetrics.training_date.desc()).limit(10).all()
        
        return jsonify({
            'metrics': [m.to_dict() for m in metrics_list]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/retrain', methods=['POST'])
def retrain_model():
    """Trigger actual model retraining using train_lightgbm.py"""
    try:
        from database import Admin, PendingAction
        
        # Check permissions
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
            
        current_admin = Admin.query.get(session['admin_id'])
        
        data = request.json or {}
        dataset_file = data.get('dataset_file') or os.path.join('models', 'dataset', 'EyeConditions_CLEAN_RISK.csv')

        # If not Super Admin, queue for approval
        if current_admin.role != 'super_admin':
            # Only analysts can request retraining; staff is read-only.
            if current_admin.role not in ('analyst',):
                return jsonify({'error': 'Unauthorized role for this action'}), 403

            pending = PendingAction(
                action_type='retrain_model',
                entity_type='ml',
                entity_id=None,
                entity_data=json.dumps({'dataset_file': dataset_file}),
                status='pending',
                requested_by=current_admin.id,
                approved_by=None,
                reason=None,
            )

            db.session.add(pending)
            db.session.commit()

            return jsonify({'message': 'Retraining request queued for approval', 'pending_action_id': pending.id}), 202

        # If Super Admin, proceed directly
        dataset_file = dataset_file
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Retrain Model',
            entity_type='ml',
            details=f'Initiated model retraining with dataset: {dataset_file}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Import and run the training function
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            from train_risk_model import train_risk_model, resolve_dataset_path

            resolved_dataset = resolve_dataset_path(dataset_file)

            # Run training (Stage-1 overall risk only)
            result = train_risk_model(dataset_path=resolved_dataset)

            # Get the newly created metrics
            new_metrics = MLMetrics.query.order_by(MLMetrics.training_date.desc()).first()

            return jsonify({
                'message': 'Risk model retrained successfully',
                'metrics': new_metrics.to_dict() if new_metrics else {},
                'training_result': {
                    'accuracy': result.accuracy,
                    'precision': result.precision,
                    'recall': result.recall,
                    'f1': result.f1,
                    'roc_auc': result.roc_auc,
                    'model_path': result.model_path,
                    'dataset_path': result.dataset_path,
                }
            }), 200

        except Exception as train_error:
            db.session.rollback()
            return jsonify({
                'error': f'Training failed: {str(train_error)}'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/upload-dataset', methods=['POST'])
def upload_dataset():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith(('.csv', '.xlsx')):
            return jsonify({'error': 'Only CSV and XLSX files allowed'}), 400
        
        # Save file
        import os
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        filepath = os.path.join('ml', 'datasets', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        # Log activity
        log = ActivityLog(
            admin_id=session.get('admin_id'),
            action='Upload Dataset',
            entity_type='ml',
            details=f'Uploaded dataset: {filename}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Dataset uploaded successfully',
            'filename': filename,
            'filepath': filepath
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
