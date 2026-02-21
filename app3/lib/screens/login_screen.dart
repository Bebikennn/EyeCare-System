import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'user_session.dart';
import '../services/api.dart';
import '../widgets/responsive.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String _message = '';

  Future<void> _login() async {
    // Validate form
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _message = '';
    });

    try {
      // Call backend API
      final response = await ApiService.loginUser(
        _emailController.text.trim(),
        _passwordController.text,
      );

      if (!mounted) return;

      if (response['status'] == 'success' && response['user'] != null) {
        // Extract user data from response
        final user = response['user'];
        final userId =
            user['user_id'] ?? user[0]; // Handle both dict and tuple formats
        final username = user['username'] ?? user[1];
        final email = user['email'] ?? user[2] ?? '';

        // Set user data in UserSession
        UserSession().setUser(
          id: userId,
          name: username,
          userEmail: email,
        );

        setState(() {
          _isLoading = false;
          _message = '✅ Login successful!';
        });

        // Navigate to the DashboardScreen
        Navigator.pushReplacementNamed(
          context,
          '/dashboard',
          arguments: {
            'username': username,
            'userId': userId,
            'email': email,
          },
        );
      } else {
        setState(() {
          _isLoading = false;
          _message = response['message'] ?? 'Login failed. Please try again.';
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _message = 'Error: ${e.toString()}';
      });
    }
  }

  String? encodeQueryParameters(Map<String, String> params) {
    return params.entries
        .map((e) =>
            '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}')
        .join('&');
  }

  Future<void> _launchSupportEmail() async {
    final Uri emailLaunchUri = Uri(
      scheme: 'mailto',
      path: 'admin@eyecare.com',
      query: encodeQueryParameters(<String, String>{
        'subject': 'Account Blocked Support Request',
        'body':
            'Hello Admin,\n\nMy account has been blocked. Please assist.\n\nUsername/Email: ${_emailController.text}'
      }),
    );

    try {
      if (!await launchUrl(emailLaunchUri)) {
        throw 'Could not launch';
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not launch email client')),
        );
      }
    }
  }

  Widget _buildMessageWidget() {
    if (_message.contains('blocked') && _message.contains('support')) {
      return Center(
        child: RichText(
          textAlign: TextAlign.center,
          text: TextSpan(
            style: const TextStyle(
              color: Colors.redAccent,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
            children: [
              const TextSpan(
                  text: 'Your account has been blocked. Please contact '),
              WidgetSpan(
                alignment: PlaceholderAlignment.baseline,
                baseline: TextBaseline.alphabetic,
                child: GestureDetector(
                  onTap: _launchSupportEmail,
                  child: const Text(
                    'support',
                    style: TextStyle(
                      color: Colors.blue,
                      decoration: TextDecoration.underline,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
              ),
              const TextSpan(text: '.'),
            ],
          ),
        ),
      );
    }

    return Text(
      _message,
      style: TextStyle(
        color: _message.contains('✅') ? Colors.green : Colors.redAccent,
        fontWeight: FontWeight.bold,
      ),
      textAlign: TextAlign.center,
    );
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Color primaryBlue = Colors.blue.shade700;

    return Scaffold(
      body: SafeArea(
        child: ResponsiveScroll(
          maxWidth: 520,
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 60),
                // Logo
                Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.visibility,
                        size: 80,
                        color: primaryBlue.withAlpha((1.0 * 255).toInt()),
                      ),
                      const SizedBox(height: 24),
                      Text(
                        'Welcome to EyeCare',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.black87,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Sign in to assess your eye health',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 50),
                // Email Field
                TextFormField(
                  controller: _emailController,
                  decoration: InputDecoration(
                    labelText: 'Email or Username',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12),
                  ),
                  keyboardType: TextInputType.emailAddress,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your email or username';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                // Password Field
                TextFormField(
                  controller: _passwordController,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12),
                  ),
                  obscureText: true,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your password';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),
                // Sign In Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _login,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: primaryBlue,
                      padding: const EdgeInsets.symmetric(vertical: 25),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            'Sign In',
                            style: TextStyle(fontSize: 16, color: Colors.white),
                          ),
                  ),
                ),
                const SizedBox(height: 16),
                // Forgot Password (Left) and Sign Up (Right)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Forgot Password Link - Left
                    TextButton(
                      onPressed: () {
                        Navigator.pushNamed(context, '/forgot-password');
                      },
                      child: Text(
                        'Forgot Password?',
                        style: TextStyle(
                          color: primaryBlue,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    // Sign Up Link - Right
                    TextButton(
                      onPressed: () {
                        Navigator.pushNamed(context, '/register');
                      },
                      child: Text(
                        'Sign Up',
                        style: TextStyle(
                          color: primaryBlue,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                // Or keep Create Account Button if you want both
                // Uncomment if you want the full Create Account button too
                /*
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pushNamed(context, '/register');
                    },
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: primaryBlue, width: 2),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: Text(
                      'Create Account',
                      style: TextStyle(
                        color: primaryBlue,
                      ),
                    ),
                  ),
                ),
                */
                const SizedBox(height: 20),
                // Message
                if (_message.isNotEmpty) _buildMessageWidget(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
