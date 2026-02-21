# System Flow Diagram for EyeCare

## Overview
This diagram illustrates the data and process flow in the EyeCare system, from user input to risk assessment output. It highlights the hybrid LightGBM and rule-based approach.

## Flow Description
1. **User Input**: User enters health/habit data via mobile app (e.g., age, sleep hours).
2. **Data Transmission**: App sends data to Flask backend via API.
3. **Preprocessing**: Backend validates and preprocesses data.
4. **Model Inference**: Hybrid model (LightGBM + rules) calculates risk.
5. **Output**: Results displayed to user with explanations.

## ASCII Art Diagram

```
[User] --> [Mobile App (Flutter)]
         |
         v
[Data Input Screen] --> [API Call to Backend]
         |
         v
[Flask Backend] --> [Validate Data]
         |
         v
[Preprocess] --> [Load LightGBM Model]
         |
         v
[Run Inference] --> [Apply Rules]
         |
         v
[Calculate Risk] --> [Generate Explanation (SHAP/LIME)]
         |
         v
[Send Response] --> [Display Results in App]
```

## Explanation
- **Mobile App**: Built with Flutter; screens like `profile.dart` handle input.
- **Backend**: Flask app with routes in `assessment.py` and `predict.py`; loads `lightgbm_model.pkl`.
- **Hybrid Model**: LightGBM for prediction, rules for safety (e.g., thresholds in `risk_score_calculator.py`).
- **Explainability**: Uses SHAP/LIME for interpretable outputs.
- **References**: Ke et al. (2017) for LightGBM; Ribeiro et al. (2016) for LIME.

## References
Ke, G., et al. (2017). LightGBM. *Advances in Neural Information Processing Systems*, 30.
Ribeiro, M. T., et al. (2016). LIME. *arXiv preprint arXiv:1602.04938*.
