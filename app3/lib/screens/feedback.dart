import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/api.dart';
import '../widgets/responsive.dart';

// -------------------------------
// FEEDBACK DATA MODELS (Updated)
// -------------------------------
class FeedbackItem {
  final int id;
  final String date;
  final int rating;
  final String category;
  final String comment;

  FeedbackItem({
    required this.id,
    required this.date,
    required this.rating,
    required this.category,
    required this.comment,
  });
}

class Category {
  final String name;
  final String icon;
  final Color color;

  Category({
    required this.name,
    required this.icon,
    required this.color,
  });
}

// -------------------------------
// FEEDBACK SCREEN (Revised)
// -------------------------------
class FeedbackScreen extends StatefulWidget {
  final ValueChanged<String> setCurrentScreen;
  final String userId;
  final String username;
  final String email;

  const FeedbackScreen({
    Key? key,
    required this.setCurrentScreen,
    required this.userId,
    required this.username,
    required this.email,
  }) : super(key: key);

  @override
  _FeedbackScreenState createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen> {
  int feedbackRating = 0;
  String feedbackCategory = '';
  String feedbackComment = '';
  bool showSuccess = false;

  String viewMode = 'submit'; // submit or history
  List<FeedbackItem> feedbackList = [];
  bool isLoading = false;
  bool isSubmitting = false;

  // -------------------------------
  // Thesis-Aligned Feedback Topics
  // -------------------------------
  final List<Category> categories = [
    Category(name: 'Assessment Accuracy', icon: '📊', color: Colors.deepPurple),
    Category(name: 'Ease of Use', icon: '👆', color: Colors.blue.shade600),
    Category(name: 'Speed of Analysis', icon: '⚡', color: Colors.cyan.shade600),
    Category(
        name: 'Clarity of Results', icon: '🔍', color: Colors.teal.shade600),
    Category(
        name: 'Lifestyle Recommendation Quality',
        icon: '💡',
        color: Colors.green.shade600),
    Category(name: 'Other', icon: '📝', color: Colors.grey.shade600),
  ];

  @override
  void initState() {
    super.initState();
    _loadFeedbackHistory();
  }

  // -------------------------------
  // LOAD FEEDBACK HISTORY
  // -------------------------------
  Future<void> _loadFeedbackHistory() async {
    setState(() => isLoading = true);

    try {
      final response = await http
          .get(
            Uri.parse('${ApiService.baseUrl}/feedback/user/${widget.userId}'),
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> feedbackData = data['feedback'] ?? [];

        setState(() {
          feedbackList = feedbackData.map((item) {
            return FeedbackItem(
              id: item['feedback_id'],
              date: item['submitted_at']?.split('T')[0] ?? '',
              rating: item['rating'],
              category: item['category'],
              comment: item['comment'],
            );
          }).toList();
        });
      }
    } catch (e) {
      print('Error loading feedback history: $e');
    } finally {
      setState(() => isLoading = false);
    }
  }

  // -------------------------------
  // SUBMIT FEEDBACK LOGIC
  // -------------------------------
  Future<void> handleSubmitFeedback() async {
    if (feedbackRating > 0 &&
        feedbackCategory.isNotEmpty &&
        feedbackComment.trim().isNotEmpty) {
      setState(() => isSubmitting = true);

      try {
        final response = await http
            .post(
              Uri.parse('${ApiService.baseUrl}/feedback'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode({
                'user_id': widget.userId,
                'username': widget.username,
                'email': widget.email,
                'rating': feedbackRating,
                'category': feedbackCategory,
                'comment': feedbackComment,
              }),
            )
            .timeout(const Duration(seconds: 10));

        if (response.statusCode == 201) {
          setState(() {
            showSuccess = true;
          });

          // Reload feedback history
          await _loadFeedbackHistory();

          Future.delayed(const Duration(seconds: 2), () {
            if (mounted) {
              setState(() {
                feedbackRating = 0;
                feedbackCategory = '';
                feedbackComment = '';
                showSuccess = false;
              });
            }
          });
        } else {
          _showErrorDialog('Failed to submit feedback. Please try again.');
        }
      } catch (e) {
        print('Error submitting feedback: $e');
        _showErrorDialog(
            'Connection error. Please check your internet connection.');
      } finally {
        setState(() => isSubmitting = false);
      }
    }
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Error'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  // -------------------------------
  // STAR WIDGET
  // -------------------------------
  Widget _renderStars(int rating, {bool interactive = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(5, (i) {
        final val = i + 1;
        final filled = val <= rating;

        final icon = Icon(
          Icons.star_rounded,
          size: interactive ? 40 : 20,
          color: filled ? Colors.amber : Colors.grey.shade300,
        );

        if (!interactive) return icon;

        return GestureDetector(
          onTap: () => setState(() => feedbackRating = val),
          child: icon,
        );
      }),
    );
  }

  String _ratingLabel(int rating) {
    switch (rating) {
      case 1:
        return '😞 Poor';
      case 2:
        return '😕 Fair';
      case 3:
        return '🙂 Good';
      case 4:
        return '😊 Very Good';
      case 5:
        return '🤩 Excellent';
      default:
        return 'Tap a star to rate';
    }
  }

  // -------------------------------
  // SUBMIT FORM UI
  // -------------------------------
  Widget _buildSubmitForm() {
    return ResponsiveScroll(
      maxWidth: 980,
      child: Column(
        children: [
          // HEADER CARD (Thesis aligned)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF7E57C2), Color(0xFF42A5F5)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(18),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.feedback, size: 48, color: Colors.white),
                SizedBox(height: 12),
                Text(
                  'Help Improve EyeCare',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 6),
                Text(
                  'Your feedback enhances our AI risk model and lifestyle recommendation accuracy. A confirmation email will be sent to ${widget.email}.',
                  style: TextStyle(color: Colors.white70),
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          // STAR RATING CARD
          Container(
            padding: const EdgeInsets.all(24),
            decoration: _cardDecoration(),
            child: Column(
              children: [
                const Text(
                  'Rate Your Experience',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 16),
                _renderStars(feedbackRating, interactive: true),
                const SizedBox(height: 12),
                Text(_ratingLabel(feedbackRating),
                    style: TextStyle(color: Colors.grey.shade600)),
              ],
            ),
          ),

          const SizedBox(height: 18),

          // CATEGORY SELECTOR
          Container(
            padding: const EdgeInsets.all(24),
            decoration: _cardDecoration(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Feedback Category',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 10,
                  children: categories.map((cat) {
                    final selected = feedbackCategory == cat.name;

                    return ChoiceChip(
                      selected: selected,
                      label: Row(
                        children: [
                          Text(cat.icon),
                          const SizedBox(width: 6),
                          Text(cat.name),
                        ],
                      ),
                      selectedColor: cat.color.withValues(alpha: .15),
                      onSelected: (_) {
                        setState(() => feedbackCategory = cat.name);
                      },
                      labelStyle: TextStyle(
                        color: selected ? cat.color : Colors.grey.shade700,
                        fontWeight: FontWeight.w600,
                      ),
                    );
                  }).toList(),
                )
              ],
            ),
          ),

          const SizedBox(height: 18),

          // COMMENT BOX
          Container(
            padding: const EdgeInsets.all(24),
            decoration: _cardDecoration(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Additional Feedback',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 16),
                TextField(
                  maxLines: 5,
                  onChanged: (text) => setState(() => feedbackComment = text),
                  decoration: InputDecoration(
                    hintText:
                        'Describe your experience with EyeCare’s risk assessment or recommendations...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
              ],
            ),
          ),

          const SizedBox(height: 24),

          // SUBMIT BUTTON
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: (feedbackRating > 0 &&
                      feedbackCategory.isNotEmpty &&
                      feedbackComment.trim().isNotEmpty &&
                      !isSubmitting)
                  ? handleSubmitFeedback
                  : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                disabledBackgroundColor: Colors.grey.shade300,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
              child: isSubmitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : const Text(
                      'Submit Feedback',
                      style: TextStyle(
                          color: Colors.white, fontWeight: FontWeight.w600),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------
  // HISTORY VIEW
  // -------------------------------
  Widget _buildHistory() {
    return ResponsiveScroll(
      maxWidth: 980,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: _gradientCard(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.history, size: 48, color: Colors.white),
                const SizedBox(height: 12),
                Text(
                  'Your Feedback History',
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 6),
                Text(
                  '${feedbackList.length} submission(s) recorded',
                  style: const TextStyle(color: Colors.white70),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          if (isLoading)
            const Center(
              child: CircularProgressIndicator(),
            )
          else if (feedbackList.isEmpty)
            Column(
              children: const [
                Icon(Icons.rate_review, size: 80, color: Color(0xFFBDBDBD)),
                SizedBox(height: 16),
                Text('No feedback added yet',
                    style: TextStyle(color: Colors.grey)),
              ],
            )
          else
            Column(
              children: feedbackList.map((fb) {
                final cat = categories.firstWhere((c) => c.name == fb.category,
                    orElse: () => categories.last);
                return Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(16),
                  decoration: _cardDecoration(),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Top Row
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(children: [
                            Text(cat.icon,
                                style: const TextStyle(fontSize: 22)),
                            const SizedBox(width: 6),
                            Text(cat.name,
                                style: TextStyle(
                                    fontWeight: FontWeight.w600,
                                    color: cat.color)),
                          ]),
                          Text(fb.date,
                              style: TextStyle(
                                  color: Colors.grey.shade500, fontSize: 12)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          _renderStars(fb.rating),
                          const SizedBox(width: 8),
                          Text(_ratingLabel(fb.rating),
                              style: const TextStyle(fontSize: 14)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(fb.comment,
                          style: TextStyle(color: Colors.grey.shade700)),
                    ],
                  ),
                );
              }).toList(),
            )
        ],
      ),
    );
  }

  // -------------------------------
  // STYLE HELPERS
  // -------------------------------
  BoxDecoration _cardDecoration() {
    return BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: Colors.grey.shade200, width: 2),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: .05),
          blurRadius: 6,
          offset: const Offset(0, 4),
        )
      ],
    );
  }

  BoxDecoration _gradientCard() {
    return BoxDecoration(
      gradient: const LinearGradient(
        colors: [Color(0xFF512DA8), Color(0xFF42A5F5)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      borderRadius: BorderRadius.circular(20),
    );
  }

  // -------------------------------
  // MAIN BUILD
  // -------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      body: Column(
        children: [
          // HEADER
          Container(
            padding: EdgeInsets.only(
                top: MediaQuery.of(context).padding.top + 14,
                bottom: 16,
                left: 16,
                right: 16),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF673AB7), Color(0xFF42A5F5)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Back Button
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white),
                  onPressed: () {
                    Navigator.pop(
                        context); // Navigate back to the previous screen
                  },
                ),
                const Text(
                  'Feedback',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() =>
                      viewMode = viewMode == 'submit' ? 'history' : 'submit'),
                  child: Text(
                    viewMode == 'submit' ? 'History' : 'Submit',
                    style: const TextStyle(color: Colors.white),
                  ),
                )
              ],
            ),
          ),

          // SUCCESS BANNER
          if (showSuccess)
            Container(
              width: double.infinity,
              color: Colors.green,
              padding: const EdgeInsets.all(16),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.check_circle, color: Colors.white),
                  SizedBox(width: 8),
                  Text(
                    "Feedback submitted successfully!",
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),

          // CONTENT
          Expanded(
            child: viewMode == 'submit' ? _buildSubmitForm() : _buildHistory(),
          ),
        ],
      ),
    );
  }
}
