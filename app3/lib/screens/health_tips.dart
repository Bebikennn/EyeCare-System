// lib/presentation/screens/healthtips/health_tips_screen.dart
import 'package:flutter/material.dart';
import '../services/health_tips_service.dart';
import 'style/app_colors.dart'; // Corrected import for AppColors
import 'style/app_text_styles.dart'; // Corrected import for AppTextStyles
import 'style/tip_card.dart'; // Corrected import for TipCard
import '../widgets/responsive.dart';

class HealthTipsScreen extends StatefulWidget {
  final String userId; // used later to fetch profile-based tips
  const HealthTipsScreen({Key? key, required this.userId}) : super(key: key);

  @override
  State<HealthTipsScreen> createState() => _HealthTipsScreenState();
}

class _HealthTipsScreenState extends State<HealthTipsScreen>
    with SingleTickerProviderStateMixin {
  // Mock categories aligned to thesis
  final List<Map<String, dynamic>> categories = [
    {
      'title': 'Healthy Vision Lifestyle',
      'emoji': '👁️',
      'color': const Color(0xFF4CAF50),
      'tips': [
        'Follow the 20-20-20 rule to reduce eye fatigue.',
        'Maintain good lighting and posture during screen work.',
        'Limit continuous screen time. Take frequent short breaks.',
      ],
    },
    {
      'title': 'Nutrition for Eye Health',
      'emoji': '🥗',
      'color': const Color(0xFF009688),
      'tips': [
        'Include leafy greens and foods rich in omega-3.',
        'Hydrate to reduce dry eye symptoms.',
        'Limit processed sugars and refined carbs.',
      ],
    },
    {
      'title': 'Lifestyle & Daily Habits',
      'emoji': '🏃',
      'color': const Color(0xFF2196F3),
      'tips': [
        'Exercise regularly to improve circulation.',
        'Quit smoking to reduce vascular damage.',
        'Target healthy sleep and maintain a stable schedule.',
      ],
    },
    {
      'title': 'Environmental Protection',
      'emoji': '🕶️',
      'color': const Color(0xFFFF9800),
      'tips': [
        'Use UV-protective sunglasses outdoors.',
        'Use humidifiers in dry environments.',
        'Reduce exposure to dust and pollutants.',
      ],
    },
  ];

  late HealthTipsService _healthTipsService;
  late Future<HealthTipsResponse> _healthTipsFuture;
  late Future<Map<String, dynamic>> _riskAssessmentFuture;

  // Simulated risk score from LightGBM+rule engine (0..1)
  double simulatedRiskScore = 0.42;

  // For header collapse
  final ScrollController _scrollController = ScrollController();
  double _headerOpacity = 1.0;

  @override
  void initState() {
    super.initState();
    _healthTipsService = HealthTipsService();

    // Get userId from widget parameter
    final userId = widget.userId;
    _healthTipsFuture = _healthTipsService.getHealthTips(userId);
    _riskAssessmentFuture = _healthTipsService.getUserRiskAssessment(userId);

    // header opacity change while scrolling
    _scrollController.addListener(() {
      final offset = _scrollController.offset;
      final newOpacity = (1.0 - (offset / 180)).clamp(0.0, 1.0);
      setState(() => _headerOpacity = newOpacity);
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: ResponsiveConstrained(
          maxWidth: 980,
          child: Column(
            children: [
            // Collapsing header with database risk score
            FutureBuilder<Map<String, dynamic>>(
              future: _riskAssessmentFuture,
              builder: (context, snapshot) {
                if (snapshot.hasData) {
                  simulatedRiskScore =
                      (snapshot.data?['risk_score'] ?? 0.42).toDouble();
                }
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 160),
                  child: _buildTopHeader(),
                );
              },
            ),

            // Body content scrollable
            Expanded(
              child: FutureBuilder<HealthTipsResponse>(
                future: _healthTipsFuture,
                builder: (context, snapshot) {
                  // Use database tips if available, otherwise use mock
                  final List<Map<String, dynamic>> displayCategories =
                      snapshot.hasData && snapshot.data!.categories.isNotEmpty
                          ? _convertHealthTipsToMock(snapshot.data!.categories)
                          : categories;

                  return CustomScrollView(
                    controller: _scrollController,
                    slivers: [
                      SliverToBoxAdapter(child: _buildIntroCard()),

                      // Animated list of tip cards
                      SliverPadding(
                        padding: const EdgeInsets.symmetric(horizontal: 0),
                        sliver: SliverList(
                          delegate: SliverChildBuilderDelegate(
                            (context, index) {
                              final item = displayCategories[index];
                              return AnimatedOpacity(
                                duration:
                                    Duration(milliseconds: 250 + (index * 40)),
                                opacity: 1,
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 16),
                                  child: TipCard(
                                    title: item['title'],
                                    emoji: item['emoji'],
                                    color: item['color'],
                                    bullets: List<String>.from(item['tips']),
                                  ),
                                ),
                              );
                            },
                            childCount: displayCategories.length,
                          ),
                        ),
                      ),

                      // Emergency / When to seek care
                      SliverToBoxAdapter(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 18),
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.red.shade50,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  decoration: BoxDecoration(
                                    color: Colors.red.shade100,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  padding: const EdgeInsets.all(10),
                                  child: const Icon(Icons.warning_amber_rounded,
                                      color: Colors.red),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: const [
                                      Text('Seek immediate care if you have:',
                                          style: TextStyle(
                                              fontWeight: FontWeight.w600)),
                                      SizedBox(height: 8),
                                      Text(
                                          'Sudden vision loss, flashing lights, severe eye pain, curtain-like shadow over vision.'),
                                    ],
                                  ),
                                )
                              ],
                            ),
                          ),
                        ),
                      ),

                      SliverToBoxAdapter(child: const SizedBox(height: 24)),
                    ],
                  );
                },
              ),
            ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTopHeader() {
    return Container(
      padding: EdgeInsets.only(
          top: MediaQuery.of(context).padding.top + 14,
          left: 16,
          right: 16,
          bottom: 18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.accent],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        ),
        borderRadius: const BorderRadius.only(
            bottomLeft: Radius.circular(24), bottomRight: Radius.circular(24)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 12,
              offset: const Offset(0, 6))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // top row
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.white),
                onPressed: () => Navigator.of(context).maybePop(),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: Opacity(
                  // the title fades out as user scrolls down
                  opacity: _headerOpacity,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('EyeCare',
                          style: AppTextStyles.heading(22)
                              .copyWith(color: Colors.white)),
                      const SizedBox(height: 2),
                      const Text('Personalized eye health guidance',
                          style: TextStyle(color: Colors.white70)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildIntroCard() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.03), blurRadius: 8)
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // large circle icon
          Container(
            width: 74,
            height: 74,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [
                AppColors.primary.withValues(alpha: 0.12),
                AppColors.accent.withValues(alpha: 0.12)
              ]),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Center(
                child: Icon(Icons.health_and_safety,
                    size: 36, color: AppColors.primary)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Why these tips matter', style: AppTextStyles.cardTitle),
                const SizedBox(height: 8),
                const Text(
                  'Tips below are aligned with factors used by EyeCare’s risk model (health and habit data). Use them between regular screenings.',
                  style: AppTextStyles.subtitle,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // Convert HealthTip objects to mock format for compatibility
  List<Map<String, dynamic>> _convertHealthTipsToMock(
      List<HealthTip> healthTips) {
    return healthTips.map((tip) {
      return {
        'title': tip.title,
        'emoji': tip.emoji,
        'color': _parseColor(tip.color),
        'tips': tip.tips,
      };
    }).toList();
  }

  // Parse color string to Color object
  Color _parseColor(String colorString) {
    try {
      if (colorString.startsWith('0xFF')) {
        return Color(int.parse(colorString));
      }
      return AppColors.primary;
    } catch (e) {
      return AppColors.primary;
    }
  }
}
