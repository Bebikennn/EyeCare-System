import 'package:flutter/material.dart';
import 'dashboard_screen.dart';
import 'user_session.dart';
import '../widgets/responsive.dart';
import 'health_tips.dart';

//
// ===============================================================
//                 DATA MODELS – THESIS ALIGNED
// ===============================================================
//

class RecommendationSet {
  final String title;
  final String message;
  final List<String> tips;

  RecommendationSet({
    required this.title,
    required this.message,
    required this.tips,
  });
}

class AssessmentHistoryItem {
  final String id;
  final String riskLevel; // low, moderate, high, critical
  final String summary; // e.g., “Healthy”, “Moderate Risk”, “High Risk”
  final String date;
  final String confidence;

  AssessmentHistoryItem({
    required this.id,
    required this.riskLevel,
    required this.summary,
    required this.date,
    required this.confidence,
  });
}

//
// SAMPLE HISTORY (replace later with database results)
//
String currentRiskLevel = "moderate";

List<AssessmentHistoryItem> historyItems = [
  AssessmentHistoryItem(
    id: "1",
    riskLevel: "low",
    summary: "Healthy Risk Profile",
    date: "2025-10-20",
    confidence: "96%",
  ),
  AssessmentHistoryItem(
    id: "2",
    riskLevel: "moderate",
    summary: "Moderate Eye Risk",
    date: "2025-09-16",
    confidence: "89%",
  ),
  AssessmentHistoryItem(
    id: "3",
    riskLevel: "high",
    summary: "High Eye Risk",
    date: "2025-08-10",
    confidence: "92%",
  ),
];

//
// Get color based on RISK LEVEL
//
Color getRiskColor(String level) {
  switch (level) {
    case "low":
      return Colors.green.shade600;
    case "moderate":
      return Colors.orange.shade600;
    case "high":
      return Colors.deepOrange.shade700;
    case "critical":
      return Colors.red.shade700;
    default:
      return Colors.grey.shade700;
  }
}

//
// Simulated navigation (replace with Navigator later)
//
void setCurrentScreen(BuildContext context, String screenName) {
  print("Navigating to $screenName");
  ScaffoldMessenger.of(
    context,
  ).showSnackBar(SnackBar(content: Text("Navigating to $screenName")));
}

//
// ===============================================================
//                 THESIS-ALIGNED RECOMMENDATIONS
// ===============================================================
//

class RecommendationsScreen extends StatelessWidget {
  final String riskLevel;
  final String? predictedDisease; // Optional: disease-specific recommendations

  const RecommendationsScreen({
    Key? key,
    required this.riskLevel,
    this.predictedDisease,
  }) : super(key: key);

  // Disease-specific recommendations
  Map<String, List<String>> get diseaseSpecificTips => {
    "Astigmatism": [
      "Get regular eye exams to monitor vision changes",
      "Wear prescribed corrective lenses consistently",
      "Ensure proper lighting when reading or using screens",
      "Take frequent breaks during close-up work",
      "Consider contact lenses or refractive surgery options",
    ],
    "Blurred Vision": [
      "Reduce continuous screen time (use 20-20-20 rule)",
      "Ensure adequate sleep (7-9 hours per night)",
      "Stay well hydrated (8 glasses of water daily)",
      "Schedule comprehensive eye examination",
      "Check for underlying conditions (diabetes, hypertension)",
    ],
    "Dry Eye": [
      "Use artificial tears or lubricating eye drops regularly",
      "Increase water intake (8+ glasses daily)",
      "Take screen breaks and blink consciously",
      "Use a humidifier in dry environments",
      "Avoid direct air flow from fans or air conditioning",
    ],
    "Hyperopia": [
      "Wear prescribed reading or multifocal glasses",
      "Ensure adequate lighting for close-up tasks",
      "Take frequent breaks during reading or screen work",
      "Get regular eye exams to update prescription",
      "Consider corrective surgery options (LASIK, PRK)",
    ],
    "Light Sensitivity": [
      "Wear sunglasses outdoors (UV protection)",
      "Reduce screen brightness and use dark mode",
      "Avoid bright fluorescent lighting",
      "Treat underlying conditions (dry eye, migraines)",
      "Use photochromic lenses that adjust to light",
    ],
    "Myopia": [
      "Wear prescribed corrective lenses consistently",
      "Increase outdoor time (2+ hours daily if possible)",
      "Reduce prolonged near work and screen time",
      "Ensure proper lighting and reading distance",
      "Monitor progression and consider control strategies",
    ],
    "Presbyopia": [
      "Use reading glasses or progressive lenses as needed",
      "Ensure bright lighting for close-up activities",
      "Hold reading material at comfortable distance",
      "Consider multifocal contact lenses",
      "Schedule regular eye exams to adjust prescription",
    ],
  };

  Map<String, RecommendationSet> get recommendationData => {
    "low": RecommendationSet(
      title: "Low Risk",
      message:
          "Your assessment indicates a low risk for eye-related complications. Continue maintaining good health and habits.",
      tips: [
        "Maintain regular sleep patterns (7–9 hours).",
        "Follow a balanced diet rich in vegetables and antioxidants.",
        "Limit continuous screen exposure; use the 20-20-20 rule.",
        "Hydrate adequately (6–8 glasses/day).",
        "Schedule routine assessments every 6–12 months.",
      ],
    ),
    "moderate": RecommendationSet(
      title: "Moderate Risk",
      message:
          "Your assessment shows a moderate eye health risk. Improving lifestyle habits can lower your risk score.",
      tips: [
        "Reduce daily screen time and take frequent breaks.",
        "Increase physical activity to at least 30 minutes/day.",
        "Improve sleep quality (avoid screens before bedtime).",
        "Monitor blood pressure and maintain a healthy BMI.",
        "Schedule an eye check-up within the next 3–6 months.",
      ],
    ),
    "high": RecommendationSet(
      title: "High Risk",
      message:
          "Your results suggest high risk for potential eye complications. Immediate lifestyle adjustments are recommended.",
      tips: [
        "Consult an eye specialist within 1–3 months.",
        "Strictly monitor blood sugar and blood pressure.",
        "Reduce high-fat and high-sodium foods.",
        "Increase outdoor activity and avoid smoking.",
        "Perform weekly self-monitoring of symptoms.",
      ],
    ),
    "critical": RecommendationSet(
      title: "Critical Risk",
      message:
          "Your risk assessment indicates a critical level. Professional evaluation and immediate health management are recommended.",
      tips: [
        "Schedule an urgent ophthalmologist consultation.",
        "Avoid prolonged screen time for several days.",
        "Maintain strict blood sugar and blood pressure control.",
        "Ensure proper hydration and adequate sleep.",
        "Follow medical guidance closely for follow-up care.",
      ],
    ),
  };

  @override
  Widget build(BuildContext context) {
    final rec =
        recommendationData[riskLevel.toLowerCase()] ??
        recommendationData["low"]!;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Column(
        children: [
          //
          // -------------------- HEADER --------------------
          //
          Container(
            color: Colors.blue.shade600,
            padding: EdgeInsets.only(
              top: MediaQuery.of(context).padding.top + 8,
              bottom: 12,
            ),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white),
                  onPressed: () {
                    final userSession = UserSession();
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
                ),
                const Text(
                  "Risk-Based Recommendations",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 18,
                  ),
                ),
              ],
            ),
          ),

          //
          // -------------------- CONTENT --------------------
          //
          Expanded(
            child: ResponsiveScroll(
              maxWidth: 980,
              child: Column(
                children: [
                  //
                  // -------- MAIN SUMMARY CARD --------
                  //
                  Container(
                    padding: const EdgeInsets.all(24),
                    margin: const EdgeInsets.only(bottom: 24),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Colors.blue.shade50, Colors.cyan.shade100],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.visibility,
                          size: 48,
                          color: getRiskColor(riskLevel),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          rec.title,
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: getRiskColor(riskLevel),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          rec.message,
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.black87,
                          ),
                        ),
                      ],
                    ),
                  ),

                  //
                  // -------- ACTIONABLE TIPS CARD --------
                  //
                  Container(
                    padding: const EdgeInsets.all(24),
                    margin: const EdgeInsets.only(bottom: 24),
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey.shade200, width: 2),
                      borderRadius: BorderRadius.circular(18),
                      color: Colors.white,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Recommended Actions",
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 16),

                        //
                        // List of tips
                        //
                        ...rec.tips.map(
                          (tip) => Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  Icons.check_circle_outline,
                                  size: 18,
                                  color: getRiskColor(riskLevel),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Text(
                                    tip,
                                    style: const TextStyle(
                                      fontSize: 14,
                                      height: 1.4,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  //
                  // -------- DISEASE-SPECIFIC RECOMMENDATIONS (if provided) --------
                  //
                  if (predictedDisease != null &&
                      diseaseSpecificTips.containsKey(predictedDisease))
                    Container(
                      padding: const EdgeInsets.all(24),
                      margin: const EdgeInsets.only(bottom: 24),
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: Colors.blue.shade200,
                          width: 2,
                        ),
                        borderRadius: BorderRadius.circular(18),
                        color: Colors.blue.shade50,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                Icons.local_hospital,
                                color: Colors.blue.shade700,
                                size: 24,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  "Tips for $predictedDisease",
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    fontSize: 16,
                                    color: Colors.blue.shade900,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),

                          //
                          // Disease-specific tips
                          //
                          ...diseaseSpecificTips[predictedDisease]!.map(
                            (tip) => Padding(
                              padding: const EdgeInsets.only(bottom: 12.0),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(
                                    Icons.medical_services_outlined,
                                    size: 18,
                                    color: Colors.blue.shade700,
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      tip,
                                      style: TextStyle(
                                        fontSize: 14,
                                        height: 1.4,
                                        color: Colors.blue.shade900,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                  //
                  // -------- IMPORTANT NOTICE --------
                  //
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.yellow.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border(
                        left: BorderSide(
                          color: Colors.yellow.shade700,
                          width: 4,
                        ),
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.warning_amber_rounded,
                          size: 30,
                          color: Colors.yellow.shade800,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            "This is an AI-assisted assessment based on health and habit data. Always consult an eye-care professional for a complete evaluation.",
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.yellow.shade800,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  //
                  // -------- BUTTONS --------
                  //
                  ElevatedButton(
                    onPressed: () {
                      final userSession = UserSession();
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => HealthTipsScreen(
                            userId: userSession.userId ?? 'Unknown',
                          ),
                        ),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange.shade600,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text(
                      "View General Eye Health Tips",
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  ElevatedButton(
                    onPressed: () {
                      final userSession = UserSession();
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(
                          builder: (_) => DashboardScreen(
                            username: userSession.username ?? 'Guest',
                            userId: userSession.userId ?? 'Unknown',
                            email: userSession.email ?? '',
                          ),
                        ),
                        (route) => false,
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue.shade600,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text(
                      "Back to Home",
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

//
// ===============================================================
//                   HISTORY SCREEN (REVISED)
// ===============================================================
//

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Column(
        children: [
          //
          // ----------------- HEADER -----------------
          //
          Container(
            color: Colors.blue.shade600,
            padding: EdgeInsets.only(
              top: MediaQuery.of(context).padding.top + 8,
              bottom: 12,
            ),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white),
                  onPressed: () => setCurrentScreen(context, "home"),
                ),
                const Text(
                  "Assessment History",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 18,
                  ),
                ),
              ],
            ),
          ),

          //
          // ----------------- HISTORY LIST -----------------
          //
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: historyItems.length,
              itemBuilder: (context, index) {
                final item = historyItems[index];

                return Container(
                  margin: const EdgeInsets.only(bottom: 14),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(color: Colors.grey.shade200, width: 2),
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.03),
                        blurRadius: 3,
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 25,
                        backgroundColor: getRiskColor(
                          item.riskLevel,
                        ).withValues(alpha: 0.15),
                        child: Icon(
                          Icons.visibility,
                          size: 28,
                          color: getRiskColor(item.riskLevel),
                        ),
                      ),
                      const SizedBox(width: 16),

                      //
                      // TEXTS
                      //
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.summary,
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 15,
                            ),
                          ),
                          Text(
                            item.date,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                      const Spacer(),
                      const Icon(
                        Icons.chevron_right,
                        color: Colors.grey,
                        size: 30,
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
