import 'package:flutter/material.dart';
import '../services/api.dart';
import '../services/assessment_detail_helper.dart';
import 'user_session.dart';
import '../widgets/responsive.dart';

class ViewHistoryAssessment extends StatefulWidget {
  final String? userId;

  const ViewHistoryAssessment({Key? key, this.userId}) : super(key: key);

  @override
  State<ViewHistoryAssessment> createState() => _ViewHistoryAssessmentState();
}

class _ViewHistoryAssessmentState extends State<ViewHistoryAssessment> {
  List<Map<String, dynamic>> assessments = [];
  bool isLoading = true;
  String errorMessage = '';

  @override
  void initState() {
    super.initState();
    loadAssessmentHistory();
  }

  Future<void> loadAssessmentHistory() async {
    setState(() {
      isLoading = true;
      errorMessage = '';
    });

    try {
      final userId = widget.userId ?? UserSession().userId ?? '';
      if (userId.isEmpty) {
        setState(() {
          errorMessage = 'User not logged in';
          isLoading = false;
        });
        return;
      }

      final result = await ApiService.getAssessmentHistory(userId);

      if (result['status'] == 'success') {
        final List<dynamic> data = result['assessments'] ?? [];
        setState(() {
          assessments =
              data.map((item) => Map<String, dynamic>.from(item)).toList();
          isLoading = false;
        });
      } else {
        setState(() {
          errorMessage = result['error'] ?? 'Failed to load assessments';
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Error: $e';
        isLoading = false;
      });
    }
  }

  Color getRiskColor(String riskLevel) {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return Colors.green;
      case 'moderate':
        return Colors.orange;
      case 'high':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData getRiskIcon(String riskLevel) {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return Icons.check_circle;
      case 'moderate':
        return Icons.warning;
      case 'high':
        return Icons.dangerous;
      default:
        return Icons.info;
    }
  }

  String formatDate(String? dateStr) {
    if (dateStr == null) return 'Unknown';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr;
    }
  }

  @override
  Widget build(BuildContext context) {
    final Color primaryBlue = Colors.blue.shade700;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text(
          'Assessment History',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: primaryBlue,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios),
          onPressed: () {
            Navigator.pushNamedAndRemoveUntil(
              context,
              '/dashboard',
              (route) => false,
              arguments: {
                'username': UserSession().username ?? 'Guest',
                'userId': UserSession().userId ?? 'Unknown',
              },
            );
          },
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : errorMessage.isNotEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error_outline,
                            size: 64, color: Colors.red[300]),
                        const SizedBox(height: 16),
                        Text(
                          errorMessage,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 16,
                            color: Colors.black54,
                          ),
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          onPressed: loadAssessmentHistory,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: primaryBlue,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                                horizontal: 24, vertical: 12),
                          ),
                        ),
                      ],
                    ),
                  ),
                )
              : assessments.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24.0),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.assignment_outlined,
                                size: 80, color: Colors.grey[300]),
                            const SizedBox(height: 16),
                            const Text(
                              'No Assessment History',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Complete an assessment to see your history here',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey[600],
                              ),
                            ),
                            const SizedBox(height: 24),
                            ElevatedButton(
                              onPressed: () {
                                if (Navigator.canPop(context)) {
                                  Navigator.pop(context);
                                }
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: primaryBlue,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 32, vertical: 14),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: const Text('Start Assessment'),
                            ),
                          ],
                        ),
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: loadAssessmentHistory,
                      child: LayoutBuilder(
                        builder: (context, constraints) {
                          final pad = responsivePagePadding(constraints.maxWidth);
                          return Align(
                            alignment: Alignment.topCenter,
                            child: ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 980),
                              child: ListView.builder(
                                padding: pad,
                                itemCount: assessments.length,
                                itemBuilder: (context, index) {
                                  final assessment = assessments[index];
                          final riskLevel =
                              assessment['risk_level'] ?? 'Unknown';
                          final predictedDisease =
                              assessment['predicted_disease'] ?? 'N/A';

                          // Safely parse confidence score
                          double confidenceValue = 0.0;
                          final confidenceRaw = assessment['confidence_score'];
                          if (confidenceRaw != null) {
                            if (confidenceRaw is num) {
                              confidenceValue = confidenceRaw.toDouble();
                            } else if (confidenceRaw is String) {
                              confidenceValue =
                                  double.tryParse(confidenceRaw) ?? 0.0;
                            }
                            // If confidence is between 0-1, multiply by 100
                            if (confidenceValue >= 0 && confidenceValue <= 1) {
                              confidenceValue = confidenceValue * 100;
                            }
                          }

                          final assessedAt = assessment['assessed_at'];
                          final riskScore = assessment['risk_score'] ?? 0;

                                  return Card(
                                    margin: const EdgeInsets.only(bottom: 16),
                                    elevation: 3,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: InkWell(
                                      borderRadius: BorderRadius.circular(12),
                                      onTap: () async {
                                        await AssessmentDetailHelper
                                            .showAssessmentDetail(
                                          context: context,
                                          assessmentId: assessment
                                              ['assessment_id'].toString(),
                                          formatDate: formatDate,
                                        );
                                      },
                                      child: Padding(
                                        padding: const EdgeInsets.all(16),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                    // Risk Level and Disease
                                    Row(
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.all(12),
                                          decoration: BoxDecoration(
                                            color: getRiskColor(riskLevel)
                                                .withValues(alpha: 0.15),
                                            borderRadius:
                                                BorderRadius.circular(10),
                                          ),
                                          child: Icon(
                                            getRiskIcon(riskLevel),
                                            color: getRiskColor(riskLevel),
                                            size: 26,
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                riskLevel.toUpperCase(),
                                                style: TextStyle(
                                                  fontSize: 16,
                                                  fontWeight: FontWeight.bold,
                                                  color:
                                                      getRiskColor(riskLevel),
                                                ),
                                              ),
                                              const SizedBox(height: 4),
                                              Text(
                                                predictedDisease,
                                                style: TextStyle(
                                                  fontSize: 13,
                                                  color: Colors.grey[700],
                                                  fontWeight: FontWeight.w500,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                        Icon(Icons.arrow_forward_ios,
                                            size: 16, color: Colors.grey[400]),
                                      ],
                                    ),
                                    const SizedBox(height: 12),
                                    // Stats Row
                                    Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.spaceBetween,
                                      children: [
                                        _buildStatChip(
                                          icon: Icons.analytics,
                                          label:
                                              'Confidence: ${confidenceValue.toStringAsFixed(0)}%',
                                          color: primaryBlue,
                                        ),
                                        _buildStatChip(
                                          icon: Icons.assessment,
                                          label:
                                              'Risk Score: ${riskScore.toString()}/100',
                                          color: Colors.orange,
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 12),
                                    // Date
                                    Row(
                                      children: [
                                        Icon(Icons.schedule,
                                            size: 14, color: Colors.grey[600]),
                                        const SizedBox(width: 6),
                                        Text(
                                          formatDate(assessedAt),
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey[600],
                                            fontWeight: FontWeight.w500,
                                          ),
                                        ),
                                      ],
                                    ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }

  Widget _buildStatChip({
    required IconData icon,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 15, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
