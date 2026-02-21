import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/assessment_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/loading_screen.dart';
import 'screens/forgot_password_screen.dart';
import 'services/api.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize API service and auto-discover backend
  print('🔍 Initializing backend connection...');
  await ApiService.initialize();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.light,
    );

    return MaterialApp(
      title: 'EyeCare',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: colorScheme,
        scaffoldBackgroundColor: colorScheme.surface,
        appBarTheme: AppBarTheme(
          backgroundColor: colorScheme.primary,
          foregroundColor: colorScheme.onPrimary,
          centerTitle: true,
          elevation: 0,
          scrolledUnderElevation: 0,
          surfaceTintColor: Colors.transparent,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          surfaceTintColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          clipBehavior: Clip.antiAlias,
        ),
        dialogTheme: DialogThemeData(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          surfaceTintColor: Colors.transparent,
        ),
        snackBarTheme: const SnackBarThemeData(
          behavior: SnackBarBehavior.floating,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: colorScheme.surfaceContainerHighest,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 14,
            vertical: 14,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(color: colorScheme.primary, width: 2),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size.fromHeight(52),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
            textStyle: const TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 16,
            ),
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            minimumSize: const Size.fromHeight(52),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
            textStyle: const TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 16,
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            minimumSize: const Size.fromHeight(52),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
            side: BorderSide(color: colorScheme.outline),
            textStyle: const TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 16,
            ),
          ),
        ),
      ),
      initialRoute: '/login',
      routes: {
        '/login': (ctx) => const LoginScreen(),
        '/register': (ctx) => const RegisterScreen(),
        '/forgot-password': (ctx) => const ForgotPasswordScreen(),
        '/dashboard': (ctx) {
          final args =
              ModalRoute.of(ctx)?.settings.arguments as Map<String, dynamic>?;
          final username = args?['username'] ?? 'Guest';
          final userId = args?['userId'] ?? 'Unknown';
          final email = args?['email'] ?? '';
          return DashboardScreen(
            username: username,
            userId: userId,
            email: email,
          );
        },
        '/AssessmentScreen': (ctx) {
          final args =
              ModalRoute.of(ctx)?.settings.arguments as Map<String, dynamic>?;
          final userId = args?['userId'] ?? 'Unknown';
          return AssessmentScreen(userId: userId);
        },
        '/loading': (ctx) => const LoadingScreen(), // Add the loading route
      },
    );
  }
}
