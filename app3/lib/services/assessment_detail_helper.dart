import 'dart:convert';
import 'package:flutter/material.dart';
import '../screens/assessment_result_screen.dart';
import 'api.dart';

class AssessmentDetailHelper {
  /// Safely parse recommendations from backend response
  static List<String> parseRecommendations(dynamic recsData) {
    final recommendations = <String>[];

    if (recsData == null) return recommendations;

    try {
      if (recsData is List) {
        for (var r in recsData) {
          if (r is Map) {
            // Try different possible keys
            if (r.containsKey('recommendation_text')) {
              recommendations.add(r['recommendation_text'].toString());
            } else if (r.containsKey('text')) {
              recommendations.add(r['text'].toString());
            } else if (r.containsKey('recommendation')) {
              recommendations.add(r['recommendation'].toString());
            }
          } else if (r is String) {
            recommendations.add(r);
          }
        }
      } else if (recsData is String) {
        // Try to parse as JSON
        try {
          final parsed = jsonDecode(recsData);
          if (parsed is List) {
            return parseRecommendations(parsed);
          }
        } catch (_) {
          recommendations.add(recsData);
        }
      }
    } catch (e) {
      print('Error parsing recommendations: $e');
    }

    return recommendations;
  }

  /// Safely parse disease probabilities from backend response
  static Map<String, double> parseDiseaseProbabilities(dynamic probsData) {
    final diseaseProbs = <String, double>{};

    if (probsData == null) return diseaseProbs;

    try {
      if (probsData is String) {
        // Try to parse JSON string
        try {
          final parsed = jsonDecode(probsData);
          return parseDiseaseProbabilities(parsed);
        } catch (e) {
          print('Error parsing JSON disease probabilities string: $e');
        }
      } else if (probsData is Map) {
        probsData.forEach((key, value) {
          try {
            final doubleValue = _toDouble(value);
            if (doubleValue != null) {
              diseaseProbs[key.toString()] = doubleValue;
            }
          } catch (e) {
            print('Error parsing disease probability for $key: $e');
          }
        });
      }
    } catch (e) {
      print('Error parsing disease probabilities: $e');
    }

    return diseaseProbs;
  }

  /// Safely convert various types to double
  static double? _toDouble(dynamic value) {
    if (value == null) return null;

    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is num) return value.toDouble();

    if (value is String) {
      return double.tryParse(value);
    }

    return null;
  }

  /// Fetch assessment detail and navigate to result screen
  static Future<void> showAssessmentDetail({
    required BuildContext context,
    required String assessmentId,
    required String Function(String?) formatDate,
  }) async {
    print('showAssessmentDetail called with assessmentId: $assessmentId');

    // Show loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(
        child: CircularProgressIndicator(),
      ),
    );

    try {
      // Fetch detailed assessment data
      print('Fetching assessment detail...');
      final detailResult = await ApiService.getAssessmentDetail(assessmentId);
      print('Detail result: $detailResult');

      // Close loading dialog
      if (context.mounted) {
        Navigator.pop(context);
      }

      if (detailResult['status'] == 'success') {
        print('Detail fetch successful');
        final fullAssessment = detailResult['assessment'];
        print('Full assessment data: $fullAssessment');

        // Parse all fields safely
        final riskLevel = fullAssessment['risk_level']?.toString() ?? 'Unknown';
        final predictedDisease =
            fullAssessment['predicted_disease']?.toString() ?? 'N/A';

        final confidenceScore =
            _toDouble(fullAssessment['confidence_score']) ?? 0.0;
        final riskScore = _toDouble(fullAssessment['risk_score']);

        final assessedAt = fullAssessment['assessed_at']?.toString();
        final assessmentIdStr = fullAssessment['assessment_id']?.toString();

        print(
            'Parsed values - riskLevel: $riskLevel, confidence: $confidenceScore, riskScore: $riskScore');

        // Parse recommendations
        final recommendationsStrings =
            parseRecommendations(fullAssessment['recommendations']);
        print('Parsed recommendations count: ${recommendationsStrings.length}');

        // Convert recommendations to Map format expected by AssessmentResultScreen
        final recommendationsMaps = recommendationsStrings
            .map((rec) => {
                  'recommendation_text': rec,
                  'text': rec,
                  'category': 'General',
                  'priority': 'Medium',
                })
            .toList();

        // Parse disease probabilities
        final diseaseProbs =
            parseDiseaseProbabilities(fullAssessment['disease_probabilities']);
        print('Parsed disease probabilities count: ${diseaseProbs.length}');

        if (context.mounted) {
          print('Navigating to AssessmentResultScreen...');
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => AssessmentResultScreen(
                riskLevel: riskLevel,
                confidence: confidenceScore / 100, // Convert to 0-1 range
                factors: [
                  RiskFactor(
                    name: predictedDisease,
                    detected: true,
                    percentage: confidenceScore,
                  ),
                ],
                modelUsed: 'LightGBM ML Model',
                date: formatDate(assessedAt),
                processingTime: 1.2,
                assessmentId: assessmentIdStr,
                riskScore: riskScore,
                recommendations: recommendationsMaps,
                diseasesProbabilities: diseaseProbs,
              ),
            ),
          );
          print('Navigation completed');
        }
      } else {
        print('Detail fetch failed: ${detailResult['error']}');
        // Show error
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'Failed to load assessment details: ${detailResult['error'] ?? 'Unknown error'}',
              ),
              backgroundColor: Colors.red,
              duration: const Duration(seconds: 4),
            ),
          );
        }
      }
    } catch (e, stackTrace) {
      print('Error in showAssessmentDetail: $e');
      print('Stack trace: $stackTrace');

      // Close loading dialog if still open
      if (context.mounted) {
        try {
          Navigator.pop(context);
        } catch (_) {
          // Dialog might already be closed
        }
      }

      // Show error
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading assessment: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }
}
