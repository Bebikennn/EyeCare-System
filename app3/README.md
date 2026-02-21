# EyeCare: Intelligent Eye Disease Risk Assessment System

Full-stack application for eye health risk assessment using LightGBM ML and rule-based approaches.

## Quick Start

### 1. Database Setup
Open phpMyAdmin → SQL tab → Copy/paste content from `eyecare_backend/sql/eyecare_database.sql` → Click Go

### 2. Backend
```powershell
cd eyecare_backend
D:/Users/johnv/Projects/app3/.venv/Scripts/python.exe app.py
```
Server runs on http://localhost:5000

### 3. Frontend
Update `lib/services/api.dart` baseUrl to:
- Android emulator: `http://10.0.2.2:5000`
- Physical device: `http://YOUR_IP:5000`
Then run: `flutter run`

### 4. Test Login
- Username: `testuser`
- Password: `testpass123`

## Key Features
✅ ML-powered risk assessment (LightGBM)
✅ Personalized recommendations
✅ Assessment history tracking
✅ Health tips database
✅ User profile management

## API Endpoints
- `POST /api/assessment/submit` - Submit assessment
- `GET /api/assessment/history/<user_id>` - Get history
- `POST /register` - Register user
- `POST /login` - Login
- `GET /user/health_tips/<user_id>` - Get tips

## Troubleshooting
- **Backend won't start**: Check XAMPP MySQL is running
- **Frontend can't connect**: Update baseUrl in api.dart
- **Model not found**: Already trained at `models/lightgbm_model.pkl`

See full documentation in eyecare_backend/sql/ folder.
