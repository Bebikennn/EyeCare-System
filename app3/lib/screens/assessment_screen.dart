import 'package:flutter/material.dart';
import 'assessment_result_screen.dart';
import '../services/api.dart';
import '../widgets/responsive.dart';

// MODEL
class Question {
  final String id;
  final String text;
  final String type;
  final List<String>? options;
  final String? guide; // Help text for the question

  Question({
    required this.id,
    required this.text,
    required this.type,
    this.options,
    this.guide,
  });
}

class AssessmentScreen extends StatefulWidget {
  final String userId;

  const AssessmentScreen({Key? key, required this.userId}) : super(key: key);

  @override
  State<AssessmentScreen> createState() => _AssessmentScreenState();
}

class _AssessmentScreenState extends State<AssessmentScreen> {
  int index = 0;
  Map<String, dynamic> answers = {};
  Map<String, TextEditingController> controllers = {};
  bool hasCompletedAssessmentBefore = false;
  bool isCheckingHistory = true;
  List<Question> displayQuestions = [];
  bool isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _checkAssessmentHistory();
  }

  Future<void> _checkAssessmentHistory() async {
    try {
      // Check if user has taken assessment before
      final historyResult = await ApiService.getAssessmentHistory(
        widget.userId,
      );

      if (historyResult['status'] == 'success') {
        final List<dynamic> assessments = historyResult['assessments'] ?? [];
        hasCompletedAssessmentBefore = assessments.isNotEmpty;

        // If user has completed assessment before, fetch their age and gender from profile
        if (hasCompletedAssessmentBefore) {
          final profileResult = await ApiService.getUserProfile(widget.userId);
          if (profileResult['status'] == 'success') {
            final healthData = profileResult['health'] ?? {};
            final age = healthData['age'];
            final gender = healthData['gender'];
            if (age != null) {
              // Store age from profile
              answers['Age'] = age.toString();
            }
            if (gender != null) {
              // Store gender from profile
              answers['Gender'] = gender.toString();
            }
          }
        }
      }
    } catch (e) {
      print('Error checking assessment history: $e');
    }

    setState(() {
      // Build questions list based on whether user has completed assessment before
      displayQuestions = hasCompletedAssessmentBefore
          ? questions.where((q) => q.id != 'Age' && q.id != 'Gender').toList()
          : questions;

      // Initialize controllers for all number type questions
      for (var question in displayQuestions) {
        if (question.type == 'number') {
          controllers[question.id] = TextEditingController(
            text: answers[question.id]?.toString() ?? '',
          );
        }
      }
      // Initialize controllers for weight and height
      controllers['weight'] = TextEditingController(
        text: answers['weight']?.toString() ?? '',
      );
      controllers['height'] = TextEditingController(
        text: answers['height']?.toString() ?? '',
      );

      isCheckingHistory = false;
    });
  }

  @override
  void dispose() {
    // Dispose all controllers
    controllers.values.forEach((controller) => controller.dispose());
    super.dispose();
  }

  final List<Question> questions = [
    Question(
      id: "Age",
      text: "What is your age?",
      type: "number",
      guide: "Enter your current age in years (e.g., 28)",
    ),
    Question(
      id: "Gender",
      text: "What is your gender?",
      type: "radio",
      options: ["Male", "Female"],
      guide: "Select your biological gender for accurate health assessment",
    ),
    Question(
      id: "BMI",
      text: "Enter your Weight and Height",
      type: "weight_height",
      guide:
          "BMI will be calculated automatically. Weight in kg, Height in cm. Example: 70kg, 175cm = BMI 22.86",
    ),
    Question(
      id: "Screen_Time_Hours",
      text: "Daily screen time (hours)?",
      type: "number",
      guide:
          "Include time spent on phones, computers, tablets, and TV. Average 6-8 hours is common for office workers.",
    ),
    Question(
      id: "Sleep_Hours",
      text: "Sleep hours per night?",
      type: "number",
      guide:
          "Enter average hours of sleep you get per night. Healthy range: 7-9 hours.",
    ),
    Question(
      id: "Smoker",
      text: "Do you smoke?",
      type: "radio",
      options: ["Yes", "No"],
      guide:
          "Include cigarettes, cigars, or any tobacco products. Smoking affects eye health significantly.",
    ),
    Question(
      id: "Alcohol_Use",
      text: "Do you drink alcohol?",
      type: "radio",
      options: ["Yes", "No"],
      guide:
          "Regular alcohol consumption can impact eye health and overall wellness.",
    ),
    Question(
      id: "Diabetes",
      text: "Do you have diabetes?",
      type: "radio",
      options: ["Yes", "No"],
      guide:
          "Diabetes can lead to diabetic retinopathy, a major cause of vision loss. Include Type 1 or Type 2.",
    ),
    Question(
      id: "Hypertension",
      text: "Do you have hypertension?",
      type: "radio",
      options: ["Yes", "No"],
      guide:
          "High blood pressure (>140/90 mmHg) can damage blood vessels in your eyes.",
    ),
    Question(
      id: "Family_History_Eye_Disease",
      text: "Family history of eye disease?",
      type: "radio",
      options: ["Yes", "No"],
      guide:
          "Include glaucoma, macular degeneration, or other eye conditions in parents/siblings.",
    ),
    Question(
      id: "Outdoor_Exposure_Hours",
      text: "Outdoor exposure (hours/day)?",
      type: "number",
      guide:
          "Average hours spent outdoors daily. UV exposure affects eye health; protection is important.",
    ),
    Question(
      id: "Diet_Score",
      text: "How healthy is your diet? (1–10)",
      type: "number",
      guide:
          "Rate your nutrition: 1 = Poor (fast food, sugary), 5 = Average (mixed), 10 = Excellent (fruits, vegetables, omega-3).",
    ),
    Question(
      id: "Water_Intake_Liters",
      text: "Water intake (liters/day)?",
      type: "number",
      guide:
          "Daily water consumption in liters. Recommended: 2-3 liters for proper eye hydration and health.",
    ),
    Question(
      id: "Glasses_Usage",
      text: "Do you use prescription glasses?",
      type: "radio",
      options: ["Yes", "No"],
      guide:
          "Include prescription glasses or contact lenses for vision correction.",
    ),
    Question(
      id: "Previous_Eye_Surgery",
      text: "Previous eye surgery?",
      type: "radio",
      options: ["Yes", "No"],
      guide: "Any previous eye surgeries including LASIK or other procedures.",
    ),
    Question(
      id: "Physical_Activity_Level",
      text: "Physical activity level?",
      type: "radio",
      options: ["Low", "Moderate", "High"],
      guide:
          "Low = Sedentary (<30 min/week), Moderate = 2-3 days/week, High = Daily exercise. Activity improves blood flow to eyes.",
    ),
  ];

  // Submit assessment to backend API
  Future<Map<String, dynamic>> submitAssessment() async {
    // Map Dart answers to API format
    int yesNo01(String? v) => (v == 'Yes') ? 1 : 0;

    int physicalActivityLevel(String? v) {
      switch (v) {
        case 'Low':
          return 1;
        case 'Moderate':
          return 2;
        case 'High':
          return 3;
        default:
          return 2;
      }
    }

    Map<String, dynamic> assessmentData = {
      "Age": int.tryParse(answers["Age"]?.toString() ?? "0") ?? 0,
      "Gender": answers["Gender"] ?? "Male",
      "BMI": double.tryParse(answers["BMI"]?.toString() ?? "0") ?? 0,
      "Screen_Time_Hours":
          double.tryParse(answers["Screen_Time_Hours"]?.toString() ?? "0") ?? 0,
      "Sleep_Hours":
          double.tryParse(answers["Sleep_Hours"]?.toString() ?? "0") ?? 0,
      "Smoker": yesNo01(answers["Smoker"]?.toString()),
      "Alcohol_Use": yesNo01(answers["Alcohol_Use"]?.toString()),
      "Diabetes": yesNo01(answers["Diabetes"]?.toString()),
      "Hypertension": yesNo01(answers["Hypertension"]?.toString()),
      "Family_History_Eye_Disease": yesNo01(
        answers["Family_History_Eye_Disease"]?.toString(),
      ),
      "Outdoor_Exposure_Hours":
          double.tryParse(
            answers["Outdoor_Exposure_Hours"]?.toString() ?? "0",
          ) ??
          0,
      "Diet_Score": int.tryParse(answers["Diet_Score"]?.toString() ?? "5") ?? 5,
      "Water_Intake_Liters":
          double.tryParse(answers["Water_Intake_Liters"]?.toString() ?? "0") ??
          0,
      "Glasses_Usage": yesNo01(answers["Glasses_Usage"]?.toString()),
      "Previous_Eye_Surgery": yesNo01(
        answers["Previous_Eye_Surgery"]?.toString(),
      ),
      "Physical_Activity_Level": physicalActivityLevel(
        answers["Physical_Activity_Level"]?.toString(),
      ),
    };

    print('Submitting assessment for user: ${widget.userId}');
    print('Assessment data: $assessmentData');

    try {
      final result = await ApiService.submitAssessment(
        widget.userId,
        assessmentData,
      );
      print('Backend response: $result');
      return result;
    } catch (e) {
      print('Exception during assessment: $e');
      return {"status": "error", "error": e.toString()};
    }
  }

  Future<bool?> _showQuitConfirmationDialog() async {
    return showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 28),
              SizedBox(width: 12),
              Text('Quit Assessment?'),
            ],
          ),
          content: Text(
            'Are you sure you want to quit this assessment? Your progress will be lost.',
            style: TextStyle(fontSize: 16),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
                foregroundColor: Theme.of(context).colorScheme.onError,
              ),
              child: Text('Quit'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _showAnalyzingDialog() async {
    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) {
        return PopScope(
          canPop: false,
          child: Material(
            type: MaterialType.transparency,
            child: Center(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 32),
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: const [
                    BoxShadow(color: Colors.black12, blurRadius: 10),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 16),
                    Text(
                      'Analyzing...',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    // Show loading while checking history
    if (isCheckingHistory) {
      return Scaffold(
        backgroundColor: Colors.grey.shade50,
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final question = displayQuestions[index];

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (!didPop) {
          // Show confirmation dialog when user tries to go back
          final shouldPop = await _showQuitConfirmationDialog() ?? false;
          if (shouldPop && mounted) {
            Navigator.of(context).pop();
          }
        }
      },
      child: Scaffold(
        backgroundColor: Colors.grey.shade50,
        body: Column(
          children: [
            Container(
              color: Colors.blue.shade600,
              padding: EdgeInsets.only(
                top: MediaQuery.of(context).padding.top + 16,
                bottom: 16,
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      IconButton(
                        icon: Icon(Icons.arrow_back, color: Colors.white),
                        onPressed: () async {
                          final shouldQuit =
                              await _showQuitConfirmationDialog();
                          if (shouldQuit == true) {
                            Navigator.pop(context);
                          }
                        },
                      ),
                      Expanded(
                        child: Text(
                          "EyeCare Assessment",
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      SizedBox(width: 48), // Balance the back button
                    ],
                  ),
                  SizedBox(height: 12),
                  LinearProgressIndicator(
                    value: (index + 1) / displayQuestions.length,
                    color: Colors.white,
                    backgroundColor: Colors.white.withValues(alpha: 0.3),
                    minHeight: 8,
                  ),
                  SizedBox(height: 6),
                  Text(
                    "Question ${index + 1} of ${displayQuestions.length}",
                    style: TextStyle(color: Colors.white70),
                  ),
                ],
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                child: ResponsiveConstrained(
                  maxWidth: 860,
                  child: Container(
                    padding: EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(18),
                      boxShadow: [
                        BoxShadow(color: Colors.black12, blurRadius: 8),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          question.text,
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                            color: Colors.grey.shade800,
                          ),
                        ),
                        // Display guide text if available
                        if (question.guide != null) ...[
                          SizedBox(height: 12),
                          Container(
                            padding: EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.blue.shade50,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: Colors.blue.shade200,
                                width: 1,
                              ),
                            ),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  Icons.info_outline,
                                  color: Colors.blue.shade700,
                                  size: 20,
                                ),
                                SizedBox(width: 10),
                                Expanded(
                                  child: Text(
                                    question.guide!,
                                    style: TextStyle(
                                      fontSize: 14,
                                      color: Colors.blue.shade900,
                                      height: 1.4,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                        SizedBox(height: 24),
                        if (question.type == "weight_height")
                          _buildWeightHeightInput(question),
                        if (question.type == "number")
                          TextField(
                            controller: controllers[question.id]!,
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              hintText: "Enter value...",
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                            onChanged: (val) {
                              answers[question.id] = val;
                            },
                          ),
                        if (question.type == "radio")
                          Column(
                            children: question.options!.map((opt) {
                              bool selected = answers[question.id] == opt;
                              return GestureDetector(
                                onTap: () {
                                  setState(() => answers[question.id] = opt);
                                },
                                child: Container(
                                  padding: EdgeInsets.all(14),
                                  margin: EdgeInsets.only(bottom: 12),
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(14),
                                    border: Border.all(
                                      color: selected
                                          ? Colors.blue
                                          : Colors.grey.shade300,
                                      width: 2,
                                    ),
                                    color: selected
                                        ? Colors.blue.shade50
                                        : Colors.white,
                                  ),
                                  child: Row(
                                    children: [
                                      Icon(
                                        selected
                                            ? Icons.radio_button_checked
                                            : Icons.radio_button_off,
                                        color: selected
                                            ? Colors.blue
                                            : Colors.grey,
                                      ),
                                      SizedBox(width: 14),
                                      Text(opt, style: TextStyle(fontSize: 16)),
                                    ],
                                  ),
                                ),
                              );
                            }).toList(),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            Padding(
              padding: EdgeInsets.all(20),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: index == 0
                          ? null
                          : () => setState(() => index--),
                      child: Text("Back"),
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: isSubmitting
                          ? null
                          : () async {
                              if (answers[question.id] == null ||
                                  answers[question.id].toString().isEmpty)
                                return;

                              if (index == displayQuestions.length - 1) {
                                setState(() => isSubmitting = true);

                                // Show analyzing/loading screen
                                _showAnalyzingDialog();

                                // Submit to backend
                                Map<String, dynamic> result = const {
                                  'status': 'error',
                                  'error': 'Unknown error',
                                };
                                try {
                                  result = await submitAssessment();
                                } finally {
                                  if (mounted) {
                                    Navigator.of(
                                      context,
                                      rootNavigator: true,
                                    ).pop();
                                    setState(() => isSubmitting = false);
                                  }
                                }

                                print(
                                  'Assessment result: $result',
                                ); // Debug log

                                if (result['status'] == 'success') {
                                  final prediction = result['prediction'] ?? {};
                                  final recommendations =
                                      (result['recommendations']
                                          as List<dynamic>?) ??
                                      [];

                                  // Extract values with defaults
                                  final riskLevel =
                                      prediction['risk_level'] ?? 'Low';
                                  final confidence =
                                      (prediction['confidence'] is num)
                                      ? (prediction['confidence'] as num)
                                            .toDouble()
                                      : 0.0;
                                  final predictedDisease =
                                      prediction['predicted_disease'] ??
                                      'Unknown';
                                  final conditionRiskFlag =
                                      prediction['condition_risk_flag'] ??
                                      'N/A';
                                  final assessmentId = result['assessment_id'];
                                  final riskScore =
                                      (prediction['risk_score'] is num)
                                      ? (prediction['risk_score'] as num)
                                            .toDouble()
                                      : null;
                                  final diseaseProbs =
                                      prediction['per_disease_probabilities']
                                          as Map<String, dynamic>?;

                                  // Build factors list from all disease probabilities
                                  List<RiskFactor> factors = [];
                                  if (diseaseProbs != null) {
                                    diseaseProbs.forEach((disease, prob) {
                                      final probability = (prob is num)
                                          ? prob.toDouble()
                                          : 0.0;
                                      // Only show diseases with >10% probability
                                      if (probability > 0.1) {
                                        factors.add(
                                          RiskFactor(
                                            name: disease,
                                            detected:
                                                disease == predictedDisease,
                                            percentage: probability * 100,
                                          ),
                                        );
                                      }
                                    });
                                    // Sort by percentage descending
                                    factors.sort(
                                      (a, b) =>
                                          b.percentage.compareTo(a.percentage),
                                    );
                                  } else {
                                    // Fallback to single factor
                                    factors.add(
                                      RiskFactor(
                                        name: predictedDisease,
                                        detected: true,
                                        percentage: confidence * 100,
                                      ),
                                    );
                                  }

                                  Navigator.pushReplacement(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => AssessmentResultScreen(
                                        riskLevel: riskLevel,
                                        confidence: confidence,
                                        factors: factors,
                                        modelUsed:
                                            'LightGBM ML Model + Rule-Based Analysis',
                                        date: DateTime.now().toString().split(
                                          '.',
                                        )[0],
                                        processingTime: 1.2,
                                        assessmentId: assessmentId,
                                        recommendations: recommendations,
                                        diseasesProbabilities: diseaseProbs,
                                        riskScore: riskScore,
                                        predictedRisk: predictedDisease,
                                        conditionRiskFlag: conditionRiskFlag,
                                      ),
                                    ),
                                  );
                                } else {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(
                                        'Error: ${result['error'] ?? result['message'] ?? 'Failed to submit assessment'}',
                                      ),
                                      backgroundColor: Colors.red,
                                      duration: Duration(seconds: 5),
                                    ),
                                  );
                                }
                              } else {
                                setState(() => index++);
                              }
                            },
                      child: Text(
                        index == displayQuestions.length - 1
                            ? "Finish"
                            : "Next",
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Widget for Weight and Height input with automatic BMI calculation
  Widget _buildWeightHeightInput(Question question) {
    final weightController = controllers['weight']!;
    final heightController = controllers['height']!;

    void calculateBMI() {
      final weight = double.tryParse(weightController.text);
      final height = double.tryParse(heightController.text);

      if (weight != null && height != null && height > 0) {
        // Convert height from cm to meters and calculate BMI
        final heightInMeters = height / 100;
        final bmi = weight / (heightInMeters * heightInMeters);
        setState(() {
          answers['weight'] = weight;
          answers['height'] = height;
          answers[question.id] = bmi.toStringAsFixed(2);
        });
      }
    }

    return Column(
      children: [
        // Weight Input
        TextField(
          controller: weightController,
          keyboardType: TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: "Weight (kg)",
            hintText: "Enter your weight in kilograms",
            prefixIcon: Icon(Icons.monitor_weight, color: Colors.blue),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.blue, width: 2),
            ),
          ),
          onChanged: (val) {
            calculateBMI();
          },
        ),
        SizedBox(height: 16),
        // Height Input
        TextField(
          controller: heightController,
          keyboardType: TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: "Height (cm)",
            hintText: "Enter your height in centimeters",
            prefixIcon: Icon(Icons.height, color: Colors.blue),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.blue, width: 2),
            ),
          ),
          onChanged: (val) {
            calculateBMI();
          },
        ),
        // Display calculated BMI
        if (answers[question.id] != null) ...[
          SizedBox(height: 16),
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.green.shade50, Colors.green.shade100],
              ),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.green.shade300, width: 2),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.check_circle,
                  color: Colors.green.shade700,
                  size: 24,
                ),
                SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'BMI Calculated',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.green.shade700,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    Text(
                      answers[question.id].toString(),
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.green.shade900,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}
