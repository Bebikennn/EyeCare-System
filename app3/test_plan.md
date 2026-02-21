# Application Test Plan for EyeCare System

## Overview
This test plan outlines the testing approach for the EyeCare mobile health application, which assesses eye disease risk using a hybrid LightGBM and rule-based system. The plan ensures the system meets functional, performance, usability, and security requirements. Testing covers the Flutter mobile app (frontend) and Flask backend (model inference and data handling).

## Test Objectives
- Verify functional correctness: Data input, risk calculation, and result display work as expected.
- Ensure performance: Inference is fast (<2 seconds) on mobile devices.
- Validate usability: Intuitive UI for users to input data and view results.
- Confirm security: Data privacy and no unauthorized access.
- Test robustness: Handle missing data, edge cases, and errors gracefully.

## Test Scope
- **In Scope**: Mobile app screens (login, profile input, assessment view), backend APIs (assessment, prediction), model loading and inference, data storage.
- **Out of Scope**: Full clinical trials, third-party integrations (e.g., external EHR), production deployment.

## Test Strategy
- **Unit Testing**: Test individual components (e.g., risk calculator functions in `risk_score_calculator.py`).
- **Integration Testing**: Test app-backend communication (e.g., API calls in `assessment.py`).
- **System Testing**: End-to-end flows (e.g., user inputs data, views risk score).
- **User Acceptance Testing (UAT)**: Simulate real users for usability.
- **Performance Testing**: Load testing for inference speed.
- **Security Testing**: Check for data leaks or vulnerabilities.

## Test Environment
- **Mobile**: Android/iOS emulators/simulators (Flutter SDK).
- **Backend**: Local Flask server with Python 3.8+, LightGBM installed.
- **Data**: Synthetic datasets for training/testing; anonymized user data.
- **Tools**: pytest for backend, Flutter test for app, Postman for APIs.

## Test Schedule
1. **Planning Phase** (1 week): Define test cases and environment setup.
2. **Design Phase** (1 week): Write detailed test scripts.
3. **Execution Phase** (2 weeks): Run tests, log defects.
4. **Reporting Phase** (1 week): Analyze results, generate reports.

## Roles and Responsibilities
- **Tester**: Execute tests, report bugs.
- **Developer**: Fix issues, provide support.
- **Product Owner**: Review UAT, approve releases.

## Test Cases (Sample)
- **TC1: User Login**: Input valid/invalid credentials; expect success/failure.
- **TC2: Data Input**: Enter health data; check validation and storage.
- **TC3: Risk Calculation**: Submit data; verify hybrid model output (LightGBM + rules).
- **TC4: Performance**: Time inference; ensure <2s.
- **TC5: Usability**: User feedback on UI clarity.

## Execution Flow
1. **Setup**: Install app and start backend server.
2. **Preconditions**: Ensure model is trained and loaded (`lightgbm_model.pkl`).
3. **Run Tests**: Execute unit tests first, then integration, then system.
4. **Monitor**: Log errors, e.g., via Flutter debug or backend logs.
5. **Defect Management**: Use a tracker (e.g., GitHub Issues) for bugs.
6. **Retest**: After fixes, rerun failed tests.
7. **Sign-Off**: All critical tests pass.

## Reporting
- **Test Summary Report**: Pass/fail rates, defects found.
- **Metrics**: Coverage (80%+), defect density.
- **Recommendations**: For production, add automated CI/CD tests.

## Explanation
This flow ensures comprehensive testing: Start with planning to align on goals, design specific cases based on system features (e.g., hybrid model in `predict.py`), execute in a controlled environment, and report to confirm readiness. It integrates repository code (e.g., `profile.dart` for UI tests) with standards like APA-cited mHealth testing (Kumar et al., 2013).

## References
Kumar, S., et al. (2013). Mobile health technology evaluation. *American Journal of Preventive Medicine*, 45(2), 228-236.
