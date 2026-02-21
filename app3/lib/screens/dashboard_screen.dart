import 'package:flutter/material.dart';
import 'profile.dart';
import 'health_tips.dart';
import 'feedback.dart'; // Import FeedbackScreen
import 'assessment_screen.dart';
import 'view_history_assessment.dart'; // Import ViewHistoryAssessment
import 'notifications_screen.dart'; // Import NotificationScreen
import '../services/notification_service.dart' as notif_service;
import 'user_session.dart';
import '../widgets/responsive.dart';

class DashboardScreen extends StatefulWidget {
  final String username;
  final String userId;
  final String email;

  const DashboardScreen({
    super.key,
    required this.username,
    required this.userId,
    required this.email,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Color get primaryBlue => const Color(0xFF4A7FD7);

  int _unreadNotifications = 0;
  final notif_service.NotificationService _notificationService =
      notif_service.NotificationService();

  @override
  void initState() {
    super.initState();
    _loadUnreadCount();
  }

  Future<void> _loadUnreadCount() async {
    final userId = UserSession().userId;
    if (userId == null || userId.isEmpty) return;

    try {
      final response = await _notificationService.getUserNotifications(userId);
      if (response.success && mounted) {
        setState(() {
          _unreadNotifications = response.unreadCount;
        });
      }
    } catch (e) {
      print('Error loading unread count: $e');
    }
  }

  Future<void> _navigateToNotifications() async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const NotificationScreen()),
    );

    // Refresh unread count when returning from notifications
    if (mounted) {
      _loadUnreadCount();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: _buildHomePage(),
      endDrawer: _buildMenuDrawer(),
    );
  }

  Widget _buildHomePage() {
    return SafeArea(
      child: Column(
        children: [
          // Header Section with Gradient
          _buildHeader(
            title: 'EyeCare AI',
            subtitle: 'Your Eye Health Assistant',
            icon: Icons.menu,
          ),

          // Main Content - Centered Start Assessment Button
          Expanded(
            child: Center(
              child: ResponsiveConstrained(
                maxWidth: 560,
                alignment: Alignment.center,
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Large Assessment Icon
                    Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        color: const Color(0xFFE8F5E9),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: const Color(
                              0xFF4CAF50,
                            ).withValues(alpha: 0.2),
                            blurRadius: 20,
                            spreadRadius: 5,
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.remove_red_eye_outlined,
                        size: 60,
                        color: Color(0xFF4CAF50),
                      ),
                    ),
                    const SizedBox(height: 32),

                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: FilledButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) =>
                                  AssessmentScreen(userId: widget.userId),
                            ),
                          );
                        },
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Icon(Icons.assessment_outlined, size: 28),
                            SizedBox(width: 12),
                            Text(
                              'Start Assessment',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Begin your eye health evaluation',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuDrawer() {
    return Drawer(
      child: Container(
        color: Colors.white,
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [primaryBlue, primaryBlue.withValues(alpha: 0.85)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  const Icon(Icons.menu_book, size: 48, color: Colors.white),
                  const SizedBox(height: 12),
                  const Text(
                    'Menu',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Additional Features',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.85),
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF3E0),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.favorite, color: Color(0xFFF57C00)),
              ),
              title: const Text(
                'Health Tips',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('Preventive care advice'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.pop(context); // Close drawer
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => HealthTipsScreen(userId: widget.userId),
                  ),
                );
              },
            ),
            const Divider(),
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  Icons.notifications_active,
                  color: Color(0xFF4CAF50),
                ),
              ),
              title: const Text(
                'Notifications',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('View all notifications'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.pop(context); // Close drawer
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const NotificationScreen()),
                );
              },
            ),
            const Divider(),
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFE3F2FD),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  Icons.feedback_outlined,
                  color: Color(0xFF1976D2),
                ),
              ),
              title: const Text(
                'Feedback',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('Tell us what you think'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.pop(context); // Close drawer
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => FeedbackScreen(
                      setCurrentScreen: (screenName) {},
                      userId: widget.userId,
                      username: widget.username,
                      email: widget.email,
                    ),
                  ),
                );
              },
            ),
            const Divider(thickness: 2, height: 32),
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.history, color: Color(0xFF4CAF50)),
              ),
              title: const Text(
                'History',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('View assessment history'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.pop(context); // Close drawer
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) =>
                        ViewHistoryAssessment(userId: widget.userId),
                  ),
                );
              },
            ),
            const Divider(),
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFE1F5FE),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.info_outline, color: Color(0xFF0288D1)),
              ),
              title: const Text(
                'About',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('Learn about EyeCare AI'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.pop(context); // Close drawer
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => _AboutPage()),
                );
              },
            ),
            const Divider(),
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFF3E5F5),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.person, color: Color(0xFF7B1FA2)),
              ),
              title: const Text(
                'Profile',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('Manage your profile'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.pop(context); // Close drawer
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) =>
                        ProfileScreen(setCurrentScreen: (screenName) {}),
                  ),
                );
              },
            ),
            const Divider(thickness: 2, height: 32),

            // Logout Button
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16.0,
                vertical: 8.0,
              ),
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context); // Close drawer
                  // Clear session and navigate to login
                  Navigator.pushNamedAndRemoveUntil(
                    context,
                    '/login',
                    (route) => false,
                  );
                },
                icon: const Icon(Icons.logout),
                label: const Text('Logout'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.error,
                  foregroundColor: Theme.of(context).colorScheme.onError,
                  minimumSize: const Size(double.infinity, 52),
                ),
              ),
            ),
            const Divider(thickness: 2, height: 32),

            // Version Info
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16.0,
                vertical: 12.0,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'App Version',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF757575),
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'v1.0.0',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: Color(0xFF424242),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'EyeCare AI',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF757575),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Your Eye Health Assistant',
                    style: TextStyle(fontSize: 12, color: Color(0xFF9E9E9E)),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader({
    required String title,
    required String subtitle,
    required IconData icon,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 28),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [primaryBlue, primaryBlue.withValues(alpha: 0.85)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(28),
          bottomRight: Radius.circular(28),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.85),
                      fontSize: 13,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ],
              ),
              // Icons Row (Notifications, Profile, Menu)
              Row(
                children: [
                  // Notifications Icon
                  GestureDetector(
                    onTap: _navigateToNotifications,
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Stack(
                        children: [
                          Center(
                            child: Icon(
                              Icons.notifications_outlined,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                          // Notification badge - only show if there are unread notifications
                          if (_unreadNotifications > 0)
                            Positioned(
                              top: 4,
                              right: 4,
                              child: Container(
                                width: 12,
                                height: 12,
                                decoration: BoxDecoration(
                                  color: Colors.red,
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Menu Icon
                  Builder(
                    builder: (BuildContext ctx) {
                      return GestureDetector(
                        onTap: () {
                          Scaffold.of(ctx).openEndDrawer();
                        },
                        child: Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Center(
                            child: Icon(icon, color: Colors.white, size: 22),
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// About Page as separate widget
class _AboutPage extends StatelessWidget {
  const _AboutPage();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        backgroundColor: Colors.blue.shade600,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'About EyeCare',
          style: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      body: SafeArea(
        child: ResponsiveScroll(
          maxWidth: 980,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // App Icon, Name, Version
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24.0),
                child: Column(
                  children: [
                    Icon(
                      Icons.health_and_safety,
                      size: 80,
                      color: Colors.blue.shade600,
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'EyeCare Risk Assessment',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF212121),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Version 1.0.0',
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                  ],
                ),
              ),

              // About This App Card
              Container(
                padding: const EdgeInsets.all(24),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'About This App',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF212121),
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'EyeCare is an intelligent eye disease risk assessment system designed to evaluate the user’s risk level using health and lifestyle information. '
                      'The system uses a hybrid prediction model combining LightGBM with a custom rule-based engine to provide personalized insights.',
                      style: TextStyle(color: Color(0xFF424242), height: 1.4),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Rather than analyzing retinal images, this app focuses on user-provided data such as age, sleep quality, screen exposure, family history, medical conditions, and daily habits. '
                      'Using this information, it generates a personalized risk score with tailored recommendations to help prevent early eye-related complications.',
                      style: TextStyle(color: Color(0xFF424242), height: 1.4),
                    ),
                  ],
                ),
              ),

              // Research Context Card
              Container(
                padding: const EdgeInsets.all(24),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Research Context',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF212121),
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'This system is developed as part of a thesis titled "EyeCare: An Intelligent Eye Disease Risk Assessment System Using User Health and Habit Data through LightGBM and Rule-Based Approach." '
                      'The research aims to promote accessible, preventive eye care by analyzing lifestyle and health patterns that contribute to vision problems.',
                      style: TextStyle(
                        fontSize: 14,
                        color: Color(0xFF424242),
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),

              // Key Features Card
              Container(
                padding: const EdgeInsets.all(24),
                margin: const EdgeInsets.only(bottom: 24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(color: Colors.grey.shade200, width: 2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Key Features',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF212121),
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Column(
                      children: [
                        _buildFeatureRow(
                          'Risk scoring using LightGBM and rule-based logic',
                        ),
                        _buildFeatureRow(
                          'Assessment based on health and lifestyle data',
                        ),
                        _buildFeatureRow(
                          'Personalized recommendations for prevention',
                        ),
                        _buildFeatureRow(
                          'History tracking for previous assessments',
                        ),
                        _buildFeatureRow('User-friendly mobile interface'),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureRow(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle, size: 18, color: Color(0xFF4A7FD7)),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 14, color: Color(0xFF424242)),
            ),
          ),
        ],
      ),
    );
  }
}
