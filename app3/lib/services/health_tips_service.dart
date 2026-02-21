import 'package:http/http.dart' as http;
import 'dart:convert';

class HealthTip {
  final String title;
  final String emoji;
  final String color;
  final List<String> tips;

  HealthTip({
    required this.title,
    required this.emoji,
    required this.color,
    required this.tips,
  });

  factory HealthTip.fromJson(Map<String, dynamic> json) {
    return HealthTip(
      title: json['title'] ?? '',
      emoji: json['emoji'] ?? '',
      color: json['color'] ?? '0xFF4CAF50',
      tips: List<String>.from(json['tips'] ?? []),
    );
  }
}

class HealthTipsResponse {
  final List<HealthTip> categories;
  final double riskScore;
  final String riskLevel;

  HealthTipsResponse({
    required this.categories,
    required this.riskScore,
    required this.riskLevel,
  });

  factory HealthTipsResponse.fromJson(Map<String, dynamic> json) {
    final tipsData = json['tips'] as List?;
    final categories =
        tipsData?.map((tip) => HealthTip.fromJson(tip)).toList() ?? [];

    return HealthTipsResponse(
      categories: categories,
      riskScore: (json['risk_score'] ?? 0.0).toDouble(),
      riskLevel: json['risk_level'] ?? 'Unknown',
    );
  }
}

class HealthTipsService {
  static const String _baseUrl = 'http://192.168.1.11:5000';

  /// Fetch health tips and risk score for a user
  Future<HealthTipsResponse> getHealthTips(String userId) async {
    try {
      final url = '$_baseUrl/api/health-tips/user/$userId';

      final response = await http.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return HealthTipsResponse.fromJson(jsonData);
      } else {
        throw Exception('Failed to fetch health tips: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching health tips: $e');
    }
  }

  /// Fetch personalized health tips based on user's health profile
  Future<HealthTipsResponse> getPersonalizedTips(String userId) async {
    try {
      final url = '$_baseUrl/api/health-tips/user/$userId/personalized';

      final response = await http.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return HealthTipsResponse.fromJson(jsonData);
      } else {
        throw Exception(
            'Failed to fetch personalized tips: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching personalized tips: $e');
    }
  }

  /// Get risk score and assessment data for user
  Future<Map<String, dynamic>> getUserRiskAssessment(String userId) async {
    try {
      final url = '$_baseUrl/api/assessments/user/$userId/latest';

      final response = await http.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        // Return default if no assessment found
        return {
          'risk_score': 0.0,
          'risk_level': 'No Assessment',
        };
      }
    } catch (e) {
      throw Exception('Error fetching risk assessment: $e');
    }
  }
}
