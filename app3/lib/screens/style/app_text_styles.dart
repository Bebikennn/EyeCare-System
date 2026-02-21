// lib/core/constants/app_text_styles.dart
import 'package:flutter/material.dart';

class AppTextStyles {
  static const String fontFamily =
      'Poppins'; // Ensure this is set in pubspec.yaml

  static TextStyle heading(double size) => TextStyle(
        fontFamily: fontFamily,
        fontSize: size,
        fontWeight: FontWeight.w600,
        color: const Color(0xFF212121),
      );

  static const TextStyle subtitle = TextStyle(
    fontFamily: fontFamily,
    fontSize: 14,
    fontWeight: FontWeight.w400,
    color: Color(0xFF424242),
    height: 1.4,
  );

  static const TextStyle cardTitle = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
    color: Color(0xFF212121),
  );

  static const TextStyle small = TextStyle(
    fontSize: 13,
    color: Color(0xFF424242),
  );
}
