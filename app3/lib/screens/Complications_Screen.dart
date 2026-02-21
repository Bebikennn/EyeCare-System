import 'package:flutter/material.dart';
import '../widgets/responsive.dart';

// ======================================================
//  DATA MODEL — Aligned to EyeCare Thesis (Not Retinal DR)
// ======================================================
class ComplicationInfo {
  final String name;
  final String icon;
  final String description;
  final String severity;
  final Color color;

  ComplicationInfo({
    required this.name,
    required this.icon,
    required this.description,
    required this.severity,
    required this.color,
  });
}

// ======================================================
//  COMPLICATIONS SCREEN — Revised for Your Thesis
// ======================================================
class ComplicationsScreen extends StatelessWidget {
  final ValueChanged<String> setCurrentScreen;

  ComplicationsScreen({Key? key, required this.setCurrentScreen})
    : super(key: key);

  // -------------------------------------------
  // Eye Health Complications (Based on LightGBM trained model)
  // -------------------------------------------
  final List<ComplicationInfo> complicationInfo = [
    ComplicationInfo(
      name: 'Astigmatism',
      icon: '🔍',
      description:
          'Irregular curvature of the cornea or lens causes distorted or blurred vision at all distances. Poor lighting, excessive screen use, and eye fatigue worsen symptoms. Requires corrective lenses.',
      severity: 'Moderate',
      color: Colors.indigo.shade600,
    ),
    ComplicationInfo(
      name: 'Blurred Vision',
      icon: '👁️‍🗨️',
      description:
          'Loss of sharpness in eyesight, often caused by prolonged screen time, lack of sleep, dehydration, poor focusing habits, or underlying refractive errors. Usually temporary but can worsen without lifestyle changes.',
      severity: 'Mild – Moderate',
      color: Colors.blue.shade600,
    ),
    ComplicationInfo(
      name: 'Dry Eye',
      icon: '💧',
      description:
          'Insufficient tear production or poor tear quality causing burning, stinging, and redness. Reduced blinking from screen time, low water intake, and environmental factors worsen symptoms. Can lead to corneal damage if untreated.',
      severity: 'Mild – Severe',
      color: Colors.blueAccent,
    ),
    ComplicationInfo(
      name: 'Hyperopia',
      icon: '📗',
      description:
          'Farsightedness makes it difficult to focus on close objects clearly. Reading, screen work, and near tasks cause eye strain, headaches, and fatigue. Correctable with glasses or contact lenses.',
      severity: 'Mild – Moderate',
      color: Colors.green.shade600,
    ),
    ComplicationInfo(
      name: 'Light Sensitivity',
      icon: '🔆',
      description:
          'Photophobia causes discomfort or pain in bright light. Associated with screen brightness, lack of eye protection, migraines, dry eyes, or inflammation. Can temporarily reduce vision clarity and quality of life.',
      severity: 'Mild – Moderate',
      color: Colors.yellow.shade700,
    ),
    ComplicationInfo(
      name: 'Myopia',
      icon: '📘',
      description:
          'Nearsightedness makes distant objects appear blurry. Aggravated by long screen hours, close-up work, genetics, and low outdoor exposure. Progressive myopia increases risk of retinal complications. Early monitoring is crucial.',
      severity: 'Moderate – High',
      color: Colors.deepPurple.shade500,
    ),
    ComplicationInfo(
      name: 'Presbyopia',
      icon: '👓',
      description:
          'Age-related loss of ability to focus on close objects, typically starting after age 40. Natural part of aging where the eye lens becomes less flexible. Worsened by low lighting and prolonged near work. Requires reading glasses.',
      severity: 'Age-Related',
      color: Colors.brown.shade500,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Column(
        children: [
          // -------------------------------------------------
          // HEADER — Changed to Blue for EyeCare branding
          // -------------------------------------------------
          Container(
            color: Colors.blue,
            padding: EdgeInsets.only(
              top: MediaQuery.of(context).padding.top + 16,
              bottom: 16,
              left: 16,
              right: 16,
            ),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(
                    Icons.arrow_back,
                    color: Colors.white,
                    size: 24,
                  ),
                  onPressed: () => setCurrentScreen('results'),
                ),
                const SizedBox(width: 8),
                const Text(
                  'EyeCare Complications Guide',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),

          // -------------------------------------------------
          // CONTENT
          // -------------------------------------------------
          Expanded(
            child: ResponsiveScroll(
              maxWidth: 980,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header Card
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Colors.blue.shade50, Colors.blue.shade100],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Icon(Icons.visibility, size: 48, color: Colors.blue),
                        SizedBox(height: 12),
                        Text(
                          'Understanding Eye Health Risks',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Your eye health assessment is based on habits, lifestyle, and personal health data. These complications represent common outcomes linked to strain, screen time, UV exposure, and hydration.',
                          style: TextStyle(color: Colors.black54, fontSize: 14),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Complication Tiles
                  Column(
                    children: complicationInfo.map((comp) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 16.0),
                        child: ComplicationTile(complication: comp),
                      );
                    }).toList(),
                  ),

                  // Note Box
                  Container(
                    margin: const EdgeInsets.only(top: 16, bottom: 16),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border(
                        left: BorderSide(color: Colors.blue.shade600, width: 4),
                      ),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.info_outline,
                          size: 28,
                          color: Colors.blue.shade700,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'These complications are evaluated using a hybrid system combining habit-based rule analysis and machine-learning risk scoring built with LightGBM.',
                            style: TextStyle(
                              color: Colors.blue.shade800,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Buttons
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => setCurrentScreen('results'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text(
                        'Back to Results',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => setCurrentScreen('home'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.grey.shade200,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        'Home',
                        style: TextStyle(
                          color: Colors.grey.shade700,
                          fontWeight: FontWeight.w600,
                        ),
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

// ======================================================
//  TILE COMPONENT
// ======================================================
class ComplicationTile extends StatelessWidget {
  final ComplicationInfo complication;

  const ComplicationTile({Key? key, required this.complication})
    : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: Colors.grey.shade200, width: 1.8),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.06),
            spreadRadius: 1,
            blurRadius: 6,
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(complication.icon, style: const TextStyle(fontSize: 34)),
          const SizedBox(width: 16),

          // Text details
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  complication.name,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 8),

                // Severity chip
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: complication.color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    complication.severity,
                    style: TextStyle(
                      color: complication.color,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(height: 12),

                Text(
                  complication.description,
                  style: TextStyle(
                    color: Colors.grey.shade700,
                    fontSize: 14,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
