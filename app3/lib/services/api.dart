import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiService {
  static String _normalizeBaseUrl(String url) {
    final trimmed = url.trim();
    if (trimmed.isEmpty) return trimmed;
    return trimmed.endsWith('/') ? trimmed.substring(0, trimmed.length - 1) : trimmed;
  }

  // Base URL is configured at build time for web via:
  //   flutter build web --dart-define=API_BASE_URL=...
  // For safety, default to the Render backend rather than a LAN IP.
  static String _baseUrl = _normalizeBaseUrl(
    const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'https://eyecare-backend.onrender.com',
    ),
  );
  static const Duration _timeout = Duration(seconds: 10);

  static String get baseUrl => _baseUrl;

  /// Helper function to handle connection errors with user-friendly messages
  static Map<String, dynamic> _handleConnectionError(dynamic e) {
    String message;

    if (e is TimeoutException) {
      message =
          'Connection timed out. Please check your internet connection and try again.';
    } else if (e is http.ClientException) {
      message = 'Unable to connect to the server. Please try again later.';
    } else if (e.toString().contains('Connection refused')) {
      message = 'Server is not available. Please try again later.';
    } else if (e.toString().contains('SocketException') ||
        e.toString().contains('Connection')) {
      message = 'Network error. Please check your internet connection.';
    } else {
      message = 'Connection failed. Please try again.';
    }

    return {'status': 'error', 'message': message};
  }

  /// Initialize API service (call this on app startup)
  ///
  /// In production/web, the backend URL should be provided via `API_BASE_URL`
  /// at build time. We intentionally do not run local-network discovery on web.
  static Future<void> initialize() async {
    if (kIsWeb && (_baseUrl.startsWith('http://192.168.') || _baseUrl.startsWith('http://10.'))) {
      print('⚠️ Web build is using a LAN IP as API base URL: $_baseUrl');
    }
    print('🌐 Using API base URL: $_baseUrl');
  }

  /// Optional local-network discovery (disabled in this build)
  static Future<bool> discoverBackend() async {
    return false;
  }

  /// Initialize API service (call this on app startup)
  static Future<void> initialize() async {
    // Always try to auto-discover the backend on startup.
    final ok = await discoverBackend();
    if (!ok) {
      // Fall back to whatever _baseUrl is currently set to
      print('⚠️ Could not automatically discover backend. Using $_baseUrl');
    }
  }

  /// Manually set backend URL
  static Future<void> setBackendUrl(String url) async {
    _baseUrl = _normalizeBaseUrl(url);
  }

  static Future<void> testConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/test'))
          .timeout(_timeout);
      print('Backend response: ${response.body}');
    } catch (e) {
      print('Error connecting to backend: $e');
      throw e;
    }
  }

  static Future<Map<String, dynamic>> registerUser(
    String fullName,
    String username,
    String email,
    String phoneNumber,
    String password,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/register'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'full_name': fullName,
          'username': username,
          'email': email,
          'phone_number': phoneNumber,
          'password': password,
        }),
      );

      try {
        return json.decode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return {
          'status': 'error',
          'message': 'Invalid response: ${response.body}',
        };
      }
    } catch (e) {
      return _handleConnectionError(e);
    }
  }

  static Future<Map<String, dynamic>> loginUser(
    String email,
    String password,
  ) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/login'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'password': password}),
          )
          .timeout(_timeout);

      // handle non-JSON responses (like HTML 404) gracefully
      try {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return {
          'status': 'error',
          'message': 'Server error. Please try again later.',
        };
      }
    } catch (e) {
      return _handleConnectionError(e);
    }
  }

  /// Send verification code to email
  static Future<Map<String, dynamic>> sendVerificationCode(String email) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/send-verification-code'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email}),
          )
          .timeout(_timeout);

      try {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return {
          'status': 'error',
          'message': 'Server error. Please try again later.',
        };
      }
    } catch (e) {
      return _handleConnectionError(e);
    }
  }

  /// Verify the email code
  static Future<Map<String, dynamic>> verifyEmailCode(
    String email,
    String code,
  ) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/verify-code'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'code': code}),
          )
          .timeout(_timeout);

      try {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return {
          'status': 'error',
          'message': 'Server error. Please try again later.',
        };
      }
    } catch (e) {
      return _handleConnectionError(e);
    }
  }

  /// Send password reset code
  static Future<Map<String, dynamic>> forgotPassword(String email) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/forgot-password'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email}),
          )
          .timeout(_timeout);

      try {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return {
          'status': 'error',
          'message': 'Server error. Please try again later.',
        };
      }
    } catch (e) {
      return _handleConnectionError(e);
    }
  }

  /// Reset password with new password
  static Future<Map<String, dynamic>> resetPassword(
    String email,
    String newPassword,
  ) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/reset-password'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'new_password': newPassword}),
          )
          .timeout(_timeout);

      try {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return {
          'status': 'error',
          'message': 'Server error. Please try again later.',
        };
      }
    } catch (e) {
      return _handleConnectionError(e);
    }
  }

  /// Add this function to fetch health tips for a user
  static Future<Map<String, dynamic>> getHealthTips(int userId) async {
    final uri = Uri.parse('$baseUrl/user/health_tips/$userId');
    try {
      final res = await http
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(_timeout);
      if (res.statusCode != 200) {
        // try decode JSON error, otherwise return body text
        try {
          final body = jsonDecode(res.body);
          return {'error': body};
        } catch (_) {
          return {'error': 'Unable to load health tips. Please try again.'};
        }
      }
      // parse success
      final Map<String, dynamic> body =
          jsonDecode(res.body) as Map<String, dynamic>;
      return body;
    } catch (e) {
      final error = _handleConnectionError(e);
      return {'error': error['message']};
    }
  }

  /// Submit assessment and get ML prediction
  static Future<Map<String, dynamic>> submitAssessment(
    String userId,
    Map<String, dynamic> assessmentData,
  ) async {
    final uri = Uri.parse('$baseUrl/api/assessment/submit');
    try {
      assessmentData['user_id'] = userId;
      final res = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(assessmentData),
          )
          .timeout(_timeout);

      if (res.statusCode != 200) {
        try {
          final body = jsonDecode(res.body);
          return {'status': 'error', 'error': body};
        } catch (_) {
          return {
            'status': 'error',
            'error': 'Server error. Please try again.',
          };
        }
      }

      return jsonDecode(res.body) as Map<String, dynamic>;
    } catch (e) {
      final error = _handleConnectionError(e);
      return {'status': 'error', 'error': error['message']};
    }
  }

  /// Get assessment history for a user
  static Future<Map<String, dynamic>> getAssessmentHistory(
    String userId,
  ) async {
    final uri = Uri.parse('$baseUrl/api/assessment/history/$userId');
    try {
      final res = await http
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(_timeout);
      if (res.statusCode != 200) {
        return {
          'status': 'error',
          'error': 'Unable to load history. Please try again.',
        };
      }
      return jsonDecode(res.body) as Map<String, dynamic>;
    } catch (e) {
      final error = _handleConnectionError(e);
      return {'status': 'error', 'error': error['message']};
    }
  }

  /// Get user profile data
  static Future<Map<String, dynamic>> getUserProfile(String userId) async {
    final uri = Uri.parse('$baseUrl/api/user/profile?user_id=$userId');
    try {
      final res = await http
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(_timeout);
      if (res.statusCode != 200) {
        return {
          'status': 'error',
          'error': 'Unable to load profile. Please try again.',
        };
      }
      return jsonDecode(res.body) as Map<String, dynamic>;
    } catch (e) {
      final error = _handleConnectionError(e);
      return {'status': 'error', 'error': error['message']};
    }
  }

  /// Update user profile
  static Future<Map<String, dynamic>> updateUserProfile(
    String userId,
    Map<String, dynamic> profileData,
  ) async {
    final uri = Uri.parse('$baseUrl/api/user/update');
    try {
      profileData['user_id'] = userId;
      final res = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(profileData),
          )
          .timeout(_timeout);
      if (res.statusCode != 200) {
        return {
          'status': 'error',
          'error': 'Unable to update profile. Please try again.',
        };
      }
      return jsonDecode(res.body) as Map<String, dynamic>;
    } catch (e) {
      final error = _handleConnectionError(e);
      return {'status': 'error', 'error': error['message']};
    }
  }

  /// Get detailed assessment information
  static Future<Map<String, dynamic>> getAssessmentDetail(
    String assessmentId,
  ) async {
    final uri = Uri.parse('$baseUrl/api/assessment/detail/$assessmentId');
    try {
      final res = await http
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(_timeout);
      if (res.statusCode != 200) {
        return {
          'status': 'error',
          'error': 'Unable to load assessment details. Please try again.',
        };
      }
      return jsonDecode(res.body) as Map<String, dynamic>;
    } catch (e) {
      final error = _handleConnectionError(e);
      return {'status': 'error', 'error': error['message']};
    }
  }

  /// Upload profile picture
  static Future<Map<String, dynamic>> uploadProfilePicture(
    String userId,
    List<int> imageBytes,
    String fileName,
  ) async {
    final uri = Uri.parse('$baseUrl/api/user/upload-profile-picture');
    try {
      final request = http.MultipartRequest('POST', uri);
      request.fields['user_id'] = userId;
      request.files.add(
        http.MultipartFile.fromBytes(
          'profile_picture',
          imageBytes,
          filename: fileName,
        ),
      );

      final response = await request.send().timeout(_timeout);
      final responseBody = await response.stream.bytesToString();

      if (response.statusCode != 200) {
        return {
          'status': 'error',
          'error': 'Unable to upload profile picture. Please try again.',
        };
      }

      return jsonDecode(responseBody) as Map<String, dynamic>;
    } catch (e) {
      final error = _handleConnectionError(e);
      return {'status': 'error', 'error': error['message']};
    }
  }
}
