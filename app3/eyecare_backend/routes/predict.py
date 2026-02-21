"""Prediction routes.

Uses the production predictor in services.ml_predict (two-stage: ML risk + rules).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.ml_predict import predict_risk


predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")


@predict_bp.route("/risk", methods=["POST"])
def predict_risk_route():
    """Predict overall risk and (if HIGH) infer probable condition.

    Expects JSON body with keys matching dataset feature columns where possible.
    Extra keys are ignored; missing keys are imputed by the pipeline.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No JSON body provided"}), 400

    try:
        result = predict_risk(data)
        return jsonify({"status": "success", "prediction": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
