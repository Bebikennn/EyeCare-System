import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api.dart';
import 'reset_password_screen.dart';
import '../widgets/responsive.dart';

class ForgotPasswordVerifyScreen extends StatefulWidget {
  final String email;
  final String username;

  const ForgotPasswordVerifyScreen({
    super.key,
    required this.email,
    required this.username,
  });

  @override
  State<ForgotPasswordVerifyScreen> createState() =>
      _ForgotPasswordVerifyScreenState();
}

class _ForgotPasswordVerifyScreenState
    extends State<ForgotPasswordVerifyScreen> {
  final List<TextEditingController> _controllers = List.generate(
    6,
    (index) => TextEditingController(),
  );
  final List<FocusNode> _focusNodes = List.generate(
    6,
    (index) => FocusNode(),
  );

  bool _isVerifying = false;
  bool _isResending = false;
  String _message = '';
  int _resendCountdown = 0;

  @override
  void initState() {
    super.initState();
    _startResendCountdown();
  }

  void _startResendCountdown() {
    setState(() {
      _resendCountdown = 60;
    });

    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 1));
      if (mounted && _resendCountdown > 0) {
        setState(() {
          _resendCountdown--;
        });
        return true;
      }
      return false;
    });
  }

  Future<void> _verifyCode() async {
    final code = _controllers.map((c) => c.text).join();

    if (code.length != 6) {
      setState(() {
        _message = 'Please enter the complete 6-digit code';
      });
      return;
    }

    setState(() {
      _isVerifying = true;
      _message = '';
    });

    try {
      final verifyResponse =
          await ApiService.verifyEmailCode(widget.email, code);

      if (!mounted) return;

      if (verifyResponse['status'] == 'success') {
        // Code verified, navigate to reset password screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => ResetPasswordScreen(
              email: widget.email,
            ),
          ),
        );
      } else {
        setState(() {
          _message = verifyResponse['message'] ?? 'Invalid code';
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _message = 'Error: ${e.toString()}';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isVerifying = false;
        });
      }
    }
  }

  Future<void> _resendCode() async {
    if (_resendCountdown > 0) return;

    setState(() {
      _isResending = true;
      _message = '';
    });

    final response = await ApiService.forgotPassword(widget.email);

    if (!mounted) return;

    setState(() {
      _isResending = false;
    });

    if (response['status'] == 'success') {
      _startResendCountdown();
      setState(() {
        _message = '✅ New code sent to your email';
      });
    } else {
      setState(() {
        _message = response['message'] ?? 'Failed to resend code';
      });
    }
  }

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    for (var node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Color primaryBlue = Colors.blue.shade700;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Verify Code'),
        backgroundColor: primaryBlue,
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: ResponsiveScroll(
          maxWidth: 560,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 40),
              Icon(
                Icons.verified_user_outlined,
                size: 80,
                color: primaryBlue,
              ),
              const SizedBox(height: 24),
              const Text(
                'Verify Your Identity',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'We sent a 6-digit code to',
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                widget.email,
                style: TextStyle(
                  color: primaryBlue,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              // Show username
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: primaryBlue.withValues(alpha: 0.3)),
                ),
                child: Column(
                  children: [
                    const Text(
                      'Your Username:',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.black54,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      widget.username,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: primaryBlue,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),
              // 6-digit code input
              LayoutBuilder(
                builder: (context, constraints) {
                  const gap = 8.0;
                  final available = constraints.maxWidth;
                  final raw = (available - (gap * 5)) / 6;
                  final boxWidth = raw.clamp(38.0, 52.0);
                  return Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: List.generate(6, (index) {
                      return SizedBox(
                        width: boxWidth,
                        height: 60,
                        child: TextField(
                          controller: _controllers[index],
                          focusNode: _focusNodes[index],
                          textAlign: TextAlign.center,
                          keyboardType: TextInputType.number,
                          maxLength: 1,
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                          decoration: InputDecoration(
                            counterText: '',
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                              borderSide: BorderSide(color: primaryBlue),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                              borderSide:
                                  BorderSide(color: primaryBlue, width: 2),
                            ),
                          ),
                          inputFormatters: [
                            FilteringTextInputFormatter.digitsOnly,
                          ],
                          onChanged: (value) {
                            if (value.length == 1 && index < 5) {
                              _focusNodes[index + 1].requestFocus();
                            } else if (value.isEmpty && index > 0) {
                              _focusNodes[index - 1].requestFocus();
                            }

                            // Auto-verify when all digits are entered
                            if (index == 5 && value.isNotEmpty) {
                              final code =
                                  _controllers.map((c) => c.text).join();
                              if (code.length == 6) {
                                _verifyCode();
                              }
                            }
                          },
                        ),
                      );
                    }),
                  );
                },
              ),
              const SizedBox(height: 32),
              // Verify button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isVerifying ? null : _verifyCode,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: primaryBlue,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: _isVerifying
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text(
                          'Verify Code',
                          style: TextStyle(fontSize: 16, color: Colors.white),
                        ),
                ),
              ),
              const SizedBox(height: 24),
              // Resend code
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "Didn't receive the code? ",
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                  if (_resendCountdown > 0)
                    Text(
                      'Resend in ${_resendCountdown}s',
                      style: TextStyle(color: Colors.grey.shade400),
                    )
                  else
                    InkWell(
                      onTap: _isResending ? null : _resendCode,
                      child: Text(
                        _isResending ? 'Sending...' : 'Resend',
                        style: TextStyle(
                          color: primaryBlue,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 24),
              // Message
              if (_message.isNotEmpty)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: _message.contains('✅')
                        ? Colors.green.shade50
                        : Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _message,
                    style: TextStyle(
                      color: _message.contains('✅')
                          ? Colors.green.shade700
                          : Colors.red.shade700,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
