import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:flutter_nsd/flutter_nsd.dart';

class ApiService {
  // Default fallback URL - will be auto-updated when server is discovered
  static String _baseUrl = 'http://192.168.1.6:5000';
  static const Duration _timeout = Duration(seconds: 10);

  static String get baseUrl => _baseUrl;

  /// Helper function to handle connection errors with user-friendly messages
  static Map<String, dynamic> _handleConnectionError(dynamic e) {
    String message;

    if (e is SocketException) {
      message =
          'No internet connection. Please check your network and try again.';
    } else if (e is TimeoutException) {
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

  /// Auto-discover backend server on local network
  static Future<bool> discoverBackend() async {
    // mDNS/Zeroconf discovery (no hardcoded IP candidates)
    final nsd = FlutterNsd();
    StreamSubscription<NsdServiceInfo>? sub;
    Timer? timer;

    try {
      final completer = Completer<bool>();

      sub = nsd.stream.listen(
        (service) async {
          final host = _pickBestHost(service);
          final port = service.port;
          if (host == null || port == null) return;

          final testUrl = 'http://$host:$port';
          try {
            final response = await http
                .get(Uri.parse('$testUrl/test'))
                .timeout(_timeout);
            if (response.statusCode == 200) {
              _baseUrl = testUrl;
              print('✅ Backend discovered via mDNS at: $testUrl');
              if (!completer.isCompleted) completer.complete(true);
            }
          } catch (_) {
            // Ignore and keep listening
          }
        },
        onError: (e) {
          // Keep going until timeout
        },
      );

      // Service type must match backend advertisement
      await nsd.discoverServices('_eyecare._tcp.');

      timer = Timer(const Duration(seconds: 6), () {
        if (!completer.isCompleted) completer.complete(false);
      });

      final ok = await completer.future;

      await nsd.stopDiscovery();
      await sub.cancel();
      timer.cancel();

      if (!ok) {
        print('❌ Could not discover backend via mDNS. Using $_baseUrl');
      }

      return ok;
    } catch (e) {
      try {
        await nsd.stopDiscovery();
      } catch (_) {}
      try {
        await sub?.cancel();
      } catch (_) {}
      try {
        timer?.cancel();
      } catch (_) {}

      print('❌ Backend discovery failed: $e');
      return false;
    }
  }

  static String? _pickBestHost(NsdServiceInfo service) {
    // Prefer IPv4 addresses when available.
    final addrs = service.hostAddresses;
    if (addrs != null && addrs.isNotEmpty) {
      for (final a in addrs) {
        if (a.contains(':')) continue; // skip IPv6
        if (a.startsWith('169.254.')) continue; // link-local
        return a;
      }
      return addrs.first;
    }
    // Fallback to hostname (often something like "MYPC.local")
    return service.hostname;
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
    _baseUrl = url;
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
