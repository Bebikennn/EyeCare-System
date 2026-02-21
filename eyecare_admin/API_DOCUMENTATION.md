# EyeCare Admin Dashboard - API Documentation

Version: 1.0.0  
Last Updated: January 1, 2026

## Table of Contents

- [Authentication](#authentication)
- [Users API](#users-api)
- [Assessments API](#assessments-api)
- [Analytics API](#analytics-api)
- [Reports API](#reports-api)
- [Health Tips API](#health-tips-api)
- [Admin Management API](#admin-management-api)
- [Activity Logs API](#activity-logs-api)
- [Cache Management API](#cache-management-api)
- [Error Codes](#error-codes)

---

## Base URL

Development: `http://localhost:5001/api`  
Production: `https://your-domain.com/api`

## Authentication

All API endpoints (except `/auth/login`) require authentication via session cookies. The session is established after successful login.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "YourPassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "full_name": "Admin User"
  }
}
```

### Logout

```http
POST /auth/logout
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

### Check Session

```http
GET /auth/check-session
```

**Response (200 OK):**
```json
{
  "authenticated": true,
  "admin": {
    "username": "admin",
    "role": "admin"
  }
}
```

---

## Users API

### Get All Users

```http
GET /users?page=1&per_page=10&search=john&status=active
```

**Query Parameters:**
- `page` (int, optional): Page number (default: 1)
- `per_page` (int, optional): Items per page (default: 10)
- `search` (string, optional): Search by name, email, or username
- `status` (string, optional): Filter by status (active, blocked, archived)
- `start_date` (string, optional): Filter by registration date (ISO format)
- `end_date` (string, optional): Filter by registration date (ISO format)
- `sort_by` (string, optional): Sort column (default: created_at)
- `sort_order` (string, optional): asc or desc (default: desc)

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": "uuid-here",
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "status": "active",
      "created_at": "2025-12-01T10:00:00",
      "total_assessments": 5
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "pages": 10
  }
}
```

### Get User Statistics

```http
GET /users/stats
```

**Response (200 OK):**
```json
{
  "total_users": 1500,
  "active_users": 1200,
  "blocked_users": 50,
  "archived_users": 250,
  "recent_users_7_days": 35,
  "growth_percentage": 12.5
}
```

**Caching:** 5 minutes

### Create User

```http
POST /users
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "password": "SecurePass123!"
}
```

**Required Role:** super_admin

**Response (201 Created):**
```json
{
  "message": "User created successfully. Email sent.",
  "user": {
    "id": "uuid-here",
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

### Export Users

```http
GET /users/export?format=excel&status=active&start_date=2025-01-01
```

**Query Parameters:**
- `format` (string, required): csv, json, or excel
- `search`, `status`, `start_date`, `end_date`: Same as list filters

**Response:** File download (CSV/JSON/Excel)

---

## Assessments API

### Get All Assessments

```http
GET /assessments?page=1&per_page=10&risk_level=high
```

**Query Parameters:**
- `page` (int, optional): Page number
- `per_page` (int, optional): Items per page
- `risk_level` (string, optional): high, moderate, low
- `user_id` (string, optional): Filter by user
- `start_date` (string, optional): Filter by assessment date
- `end_date` (string, optional): Filter by assessment date

**Response (200 OK):**
```json
{
  "assessments": [
    {
      "id": "assessment-uuid",
      "user_name": "John Doe",
      "age": 35,
      "risk_level": "high",
      "risk_score": 0.85,
      "predicted_disease": "Glaucoma",
      "confidence": 0.92,
      "created_at": "2025-12-15T14:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 250
  }
}
```

### Get Assessment Statistics

```http
GET /assessments/stats
```

**Response (200 OK):**
```json
{
  "total_assessments": 5000,
  "high_risk": 850,
  "moderate_risk": 2100,
  "low_risk": 2050,
  "assessments_today": 45,
  "high_risk_growth": 15.3,
  "assessments_per_day": [
    {"date": "2025-12-25", "count": 42},
    {"date": "2025-12-26", "count": 38}
  ],
  "risk_distribution": {
    "low": 2050,
    "moderate": 2100,
    "high": 850
  }
}
```

**Caching:** 5 minutes

### Export Assessments

```http
GET /assessments/export?format=excel&risk_level=high&start_date=2025-12-01
```

**Query Parameters:**
- `format` (string, required): csv, json, or excel
- `risk_level`, `user_id`, `start_date`, `end_date`: Filters

**Response:** File download

---

## Analytics API

### Risk Level Trends

```http
GET /assessments/trends/risk-level?days=30
```

**Query Parameters:**
- `days` (int, optional): Number of days to analyze (default: 30)

**Response (200 OK):**
```json
{
  "trends": [
    {
      "date": "2025-12-01",
      "high": 28,
      "moderate": 45,
      "low": 32,
      "total": 105
    },
    {
      "date": "2025-12-02",
      "high": 31,
      "moderate": 42,
      "low": 35,
      "total": 108
    }
  ],
  "period": "last_30_days"
}
```

**Caching:** 10 minutes

### Disease Distribution

```http
GET /assessments/analytics/disease-distribution
```

**Response (200 OK):**
```json
{
  "distribution": [
    {"disease": "Glaucoma", "count": 342},
    {"disease": "Diabetic Retinopathy", "count": 285},
    {"disease": "Age-related Macular Degeneration", "count": 198}
  ],
  "total_diseases": 10
}
```

**Caching:** 10 minutes

### Risk Factors Analysis

```http
GET /assessments/analytics/risk-factors
```

**Response (200 OK):**
```json
{
  "total_high_risk_assessments": 850,
  "risk_factors": [
    {"factor": "Smoking", "percentage": 68.5},
    {"factor": "High Screen Time (>6hrs)", "percentage": 52.3},
    {"factor": "Alcohol Consumption", "percentage": 45.2},
    {"factor": "Low Sleep (<6hrs)", "percentage": 38.7},
    {"factor": "Low Exercise", "percentage": 31.4}
  ]
}
```

**Caching:** 10 minutes

---

## Reports API

### Dashboard Statistics

```http
GET /reports/dashboard-stats
```

**Response (200 OK):**
```json
{
  "users": {
    "total": 1500,
    "active": 1200,
    "blocked": 50,
    "recent_7_days": 35
  },
  "assessments": {
    "total": 5000,
    "recent_30_days": 850,
    "risk_distribution": {
      "low": 2050,
      "moderate": 2100,
      "high": 850
    }
  },
  "activities": {
    "total": 12000,
    "recent_30_days": 2400
  },
  "health_tips": {
    "total": 50,
    "active": 42
  }
}
```

**Caching:** 5 minutes

### Comprehensive Report

```http
GET /reports/comprehensive?format=excel&start_date=2025-12-01&end_date=2025-12-31
```

**Query Parameters:**
- `format` (string, optional): json, csv, or excel (default: json)
- `start_date` (string, optional): Start date (ISO format, default: 30 days ago)
- `end_date` (string, optional): End date (ISO format, default: today)

**Response (JSON format):**
```json
{
  "report_period": {
    "start_date": "2025-12-01",
    "end_date": "2025-12-31"
  },
  "summary": {
    "total_users": 150,
    "total_assessments": 450,
    "high_risk_assessments": 85,
    "high_risk_percentage": 18.9
  },
  "daily_breakdown": [
    {
      "date": "2025-12-01",
      "new_users": 5,
      "assessments": 15,
      "high_risk_assessments": 3
    }
  ]
}
```

**Response (Excel/CSV format):** File download

---

## Health Tips API

### Get All Health Tips

```http
GET /healthtips?category=general&status=active
```

**Query Parameters:**
- `category` (string, optional): general, diet, exercise, lifestyle
- `status` (string, optional): active, inactive
- `risk_level` (string, optional): All, Low, Moderate, High

**Response (200 OK):**
```json
{
  "health_tips": [
    {
      "id": 1,
      "title": "Protect Your Eyes from UV Rays",
      "description": "Always wear sunglasses...",
      "category": "lifestyle",
      "risk_level": "All",
      "icon": "sun",
      "status": "active"
    }
  ]
}
```

### Create Health Tip

```http
POST /healthtips
Content-Type: application/json

{
  "title": "Eye Exercise Tips",
  "description": "Follow the 20-20-20 rule...",
  "category": "exercise",
  "risk_level": "All",
  "icon": "exercise"
}
```

**Required Role:** staff, admin, super_admin

**Response (201 Created):**
```json
{
  "message": "Health tip created successfully",
  "health_tip": {
    "id": 51,
    "title": "Eye Exercise Tips"
  }
}
```

---

## Admin Management API

### Get All Admins

```http
GET /admin?role=admin&status=active
```

**Required Role:** admin, super_admin

**Response (200 OK):**
```json
{
  "admins": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "status": "active",
      "last_login": "2025-12-31T10:00:00"
    }
  ]
}
```

### Create Admin

```http
POST /admin
Content-Type: application/json

{
  "username": "newadmin",
  "email": "newadmin@example.com",
  "password": "SecurePass123!",
  "full_name": "New Admin",
  "role": "staff"
}
```

**Required Role:** super_admin

**Response (201 Created):**
```json
{
  "message": "Admin created successfully",
  "admin": {
    "id": 5,
    "username": "newadmin"
  }
}
```

---

## Activity Logs API

### Get Activity Logs

```http
GET /logs?admin_id=1&action=Create%20User&start_date=2025-12-01
```

**Query Parameters:**
- `admin_id` (int, optional): Filter by admin
- `action` (string, optional): Filter by action type
- `entity_type` (string, optional): user, admin, assessment, health_tip
- `start_date` (string, optional): Filter by date
- `end_date` (string, optional): Filter by date
- `page`, `per_page`: Pagination

**Response (200 OK):**
```json
{
  "logs": [
    {
      "id": 1234,
      "admin_username": "admin",
      "action": "Create User",
      "entity_type": "user",
      "entity_id": "uuid",
      "details": "Created user: John Doe",
      "ip_address": "192.168.1.1",
      "timestamp": "2025-12-31T15:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "total": 500
  }
}
```

---

## Cache Management API

### Get Cache Statistics

```http
GET /api/cache/stats
```

**Required Role:** admin, super_admin

**Response (200 OK):**
```json
{
  "total_entries": 15,
  "total_hits": 1247,
  "hot_keys": [
    {"key": "user_stats:abc123", "hits": 345},
    {"key": "assessment_stats:def456", "hits": 289}
  ],
  "memory_estimate_kb": 15
}
```

### Clear Cache

```http
POST /api/cache/clear
Content-Type: application/json

{
  "prefix": "user_stats"
}
```

**Request Body:**
- `prefix` (string, optional): Cache key prefix to clear. Omit to clear all cache.

**Required Role:** admin, super_admin

**Response (200 OK):**
```json
{
  "message": "Cache cleared successfully",
  "entries_removed": 3
}
```

---

## Error Codes

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": "Error message describing what went wrong",
  "details": {
    "field": "Additional validation error details"
  }
}
```

---

## Rate Limiting

**Default Limits:**
- Development: 5000 requests per day, 1000 per hour
- Production: Configurable via `RATELIMIT_DEFAULT` environment variable

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1640995200
```

---

## Pagination

Most list endpoints support pagination:

**Request:**
```http
GET /users?page=2&per_page=20
```

**Response includes:**
```json
{
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

## Best Practices

1. **Authentication**: Always include session cookies in requests
2. **Error Handling**: Check response status codes and handle errors gracefully
3. **Rate Limiting**: Implement exponential backoff for 429 responses
4. **Caching**: Leverage cached endpoints for frequently accessed data
5. **Filtering**: Use query parameters to reduce payload size
6. **Exports**: Use appropriate format based on use case:
   - CSV: Simple data analysis, Excel import
   - Excel: Complex reports with formatting
   - JSON: Programmatic consumption

---

## Support

For issues or questions:
- GitHub: [Repository URL]
- Email: support@eyecare.com
- Documentation: See `DEPLOYMENT.md` and `PERFORMANCE.md`
