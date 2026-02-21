import 'package:flutter/material.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';
import 'recommedation_screen.dart'; // Import for RecommendationScreen
import 'dashboard_screen.dart'; // Import for DashboardScreen
import 'user_session.dart'; // Corrected import for UserSession
import 'Complications_Screen.dart'; // Import for ComplicationsScreen
import '../widgets/responsive.dart';

class AssessmentResultScreen extends StatelessWidget {
  final String riskLevel;
  final double confidence;
  final List<RiskFactor> factors;
  final String modelUsed;
  final String date;
  final double processingTime;
  final String? assessmentId;
  final List<dynamic>? recommendations;
  final Map<String, dynamic>? diseasesProbabilities;
  final double? riskScore;
  final String? predictedRisk;
  final String? conditionRiskFlag;

  const AssessmentResultScreen({
    super.key,
    required this.riskLevel,
    required this.confidence,
    required this.factors,
    required this.modelUsed,
    required this.date,
    required this.processingTime,
    this.assessmentId,
    this.recommendations,
    this.diseasesProbabilities,
    this.riskScore,
    this.predictedRisk,
    this.conditionRiskFlag,
  });

  Color getRiskColor() {
    switch (riskLevel.toLowerCase()) {
      case "low":
        return Colors.green;
      case "moderate":
        return Colors.orange;
      case "high":
        return Colors.redAccent;
      default:
        return Colors.blueGrey;
    }
  }

  IconData getRiskIcon() {
    switch (riskLevel.toLowerCase()) {
      case "low":
        return Iconsax.tick_circle;
      case "moderate":
        return Iconsax.warning_2;
      case "high":
        return Iconsax.danger;
      default:
        return Iconsax.activity;
    }
  }

  String _getDiseaseMessage() {
    if (predictedRisk != null && predictedRisk!.isNotEmpty) {
      final riskLevel = this.riskLevel.toLowerCase();
      if (riskLevel == "high") {
        return "You likely have\n$predictedRisk";
      } else if (riskLevel == "moderate") {
        return "You may have\n$predictedRisk";
      } else {
        return "Low overall risk\n$predictedRisk";
      }
    }
    return riskLevel.toUpperCase();
  }

  String _getRiskBadge() {
    if (predictedRisk != null && predictedRisk!.isNotEmpty) {
      return riskLevel.toUpperCase();
    }
    return riskLevel.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final userSession = UserSession(); // Fetch current user session

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text("Assessment Results"),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: ResponsiveScroll(
          maxWidth: 980,
          child: Column(
            children: [
            // ------------------------
            //   RISK SUMMARY CARD
            // ------------------------
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border(
                  left: BorderSide(color: getRiskColor(), width: 6),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Icon(getRiskIcon(), size: 60, color: getRiskColor()),
                  const SizedBox(height: 10),
                  Text(
                    _getDiseaseMessage(),
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      height: 1.4,
                    ),
                  ),
                  Text(
                    "Confidence: ${(confidence * 100).toStringAsFixed(0)}%",
                    style: const TextStyle(fontSize: 16),
                  ),
                  if (conditionRiskFlag != null &&
                      conditionRiskFlag!.isNotEmpty &&
                      conditionRiskFlag != 'N/A')
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.blueGrey.withValues(alpha: 0.10),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          "Condition flag: ${conditionRiskFlag!}",
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.blueGrey.shade800,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  const SizedBox(height: 6),
                  Text(
                    "Probable condition only. Not a medical diagnosis.",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                    decoration: BoxDecoration(
                      color: getRiskColor().withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      _getRiskBadge(),
                      style: TextStyle(
                        color: getRiskColor(),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // ----------------------------------
            //   RELATED RISK FACTORS SECTION
            // ----------------------------------
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Iconsax.danger, color: Colors.orange),
                      SizedBox(width: 8),
                      Text(
                        "Related Risk Factors Identified",
                        style: TextStyle(
                            fontSize: 17, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  if (factors.isEmpty)
                    const Text(
                      "No risk factors detected.",
                      style: TextStyle(color: Colors.black54),
                    )
                  else
                    for (var item in factors) _RiskFactorTile(factor: item),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // ----------------------------------
            //   ALL DISEASE PROBABILITIES
            // ----------------------------------
            if (diseasesProbabilities != null &&
                diseasesProbabilities!.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Iconsax.chart_1, color: Colors.purple),
                        SizedBox(width: 8),
                        Text(
                          "Disease Probability Analysis",
                          style: TextStyle(
                              fontSize: 17, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    for (var entry in diseasesProbabilities!.entries)
                      _diseaseProbabilityBar(
                        entry.key,
                        (entry.value as num).toDouble(),
                      ),
                  ],
                ),
              ),

            if (diseasesProbabilities != null &&
                diseasesProbabilities!.isNotEmpty)
              const SizedBox(height: 18),

            // ----------------------------------
            //   RECOMMENDATIONS FROM BACKEND
            // ----------------------------------
            if (recommendations != null && recommendations!.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Iconsax.health, color: Colors.green),
                        SizedBox(width: 8),
                        Text(
                          "Personalized Recommendations",
                          style: TextStyle(
                              fontSize: 17, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    for (var rec in recommendations!)
                      _recommendationTile(
                        rec['text'] ??
                            rec['recommendation_text'] ??
                            'No recommendation',
                        rec['category'] ?? 'General',
                        rec['priority'] ?? 'Medium',
                      ),
                  ],
                ),
              ),

            if (recommendations != null && recommendations!.isNotEmpty)
              const SizedBox(height: 18),

            // ------------------------
            //   DETECTION DETAILS
            // ------------------------
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Iconsax.document, color: Colors.blue),
                      SizedBox(width: 8),
                      Text(
                        "Assessment Details",
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _detailRow("Model Used:", modelUsed),
                  _detailRow("Analysis Date:", date),
                  if (assessmentId != null)
                    _detailRow("Assessment ID:", assessmentId!.substring(0, 8)),
                  if (riskScore != null)
                    _detailRow(
                        "Risk Score:", "${riskScore!.toStringAsFixed(0)}/100"),
                  _detailRow("Processing Time:", "${processingTime}s"),
                  _detailRow(
                      "Risk Factors Evaluated:", "${factors.length} items"),
                ],
              ),
            ),

            const SizedBox(height: 22),

            // ------------------------
            //   BUTTONS
            // ------------------------
            if (recommendations == null || recommendations!.isEmpty)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    backgroundColor: Colors.blue,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                  ),
                  onPressed: () {
                    // Navigate to RecommendationScreen
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => RecommendationsScreen(
                          riskLevel: riskLevel,
                          predictedDisease: predictedRisk,
                        ),
                      ),
                    );
                  },
                  child: const Text(
                    "View Detailed Recommendations",
                    style: TextStyle(fontSize: 16, color: Colors.white),
                  ),
                ),
              ),

            if (recommendations == null || recommendations!.isEmpty)
              const SizedBox(height: 12),

            const SizedBox(height: 12),

            // View Recommendations Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => RecommendationsScreen(
                        riskLevel: riskLevel,
                        predictedDisease: predictedRisk,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.lightbulb_outline),
                label: const Text(
                  "View Recommendations",
                  style: TextStyle(fontSize: 16, color: Colors.white),
                ),
              ),
            ),

            const SizedBox(height: 12),

            // View Complications Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepOrange,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ComplicationsScreen(
                        setCurrentScreen: (screen) {
                          // Handle navigation
                          if (screen == 'results') {
                            Navigator.pop(context);
                          }
                        },
                      ),
                    ),
                  );
                },
                icon: const Icon(Iconsax.danger),
                label: const Text(
                  "View Complications",
                  style: TextStyle(fontSize: 16, color: Colors.white),
                ),
              ),
            ),

            const SizedBox(height: 12),

            TextButton(
              onPressed: () {
                // Navigate directly to DashboardScreen with the correct userId
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(
                    builder: (_) => DashboardScreen(
                      username: userSession.username ?? 'Guest',
                      userId: userSession.userId ?? 'Unknown',
                      email: userSession.email ?? '',
                    ),
                  ),
                  (route) => false, // Remove all previous routes
                );
              },
              child: const Text("Back to Home"),
            ),

            const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: const TextStyle(fontSize: 15, color: Colors.black54)),
          Text(value,
              style:
                  const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _diseaseProbabilityBar(String disease, double probability) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  disease,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                "${(probability * 100).toStringAsFixed(1)}%",
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: probability,
              minHeight: 8,
              backgroundColor: Colors.grey[200],
              color: probability > 0.5
                  ? Colors.red
                  : probability > 0.3
                      ? Colors.orange
                      : Colors.green,
            ),
          ),
        ],
      ),
    );
  }

  Widget _recommendationTile(String text, String category, String priority) {
    IconData icon;
    Color color;

    switch (category.toLowerCase()) {
      case 'lifestyle':
        icon = Iconsax.activity;
        color = Colors.orange;
        break;
      case 'medical':
        icon = Iconsax.health;
        color = Colors.red;
        break;
      case 'diet':
        icon = Iconsax.cup;
        color = Colors.green;
        break;
      case 'exercise':
        icon = Iconsax.man;
        color = Colors.blue;
        break;
      default:
        icon = Iconsax.information;
        color = Colors.grey;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        text,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        category,
                        style: TextStyle(
                          fontSize: 11,
                          color: color,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        priority,
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey[700],
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class RiskFactor {
  final String name;
  final bool detected;
  final double percentage;

  RiskFactor({
    required this.name,
    required this.detected,
    required this.percentage,
  });
}

class _RiskFactorTile extends StatelessWidget {
  final RiskFactor factor;

  const _RiskFactorTile({required this.factor});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        children: [
          Icon(
            factor.detected ? Iconsax.tick_circle : Iconsax.close_circle,
            color: factor.detected ? Colors.green : Colors.redAccent,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  factor.name,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  factor.detected ? "Detected" : "Not detected",
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: factor.detected
                  ? Colors.green.withValues(alpha: 0.12)
                  : Colors.redAccent.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              "${factor.percentage.toStringAsFixed(0)}%",
              style: TextStyle(
                color: factor.detected ? Colors.green : Colors.redAccent,
                fontWeight: FontWeight.bold,
              ),
            ),
          )
        ],
      ),
    );
  }
}
