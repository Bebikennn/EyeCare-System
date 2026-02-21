// lib/presentation/screens/healthtips/widgets/risk_chip.dart
import 'package:flutter/material.dart';
import '../style/app_colors.dart'; // Corrected import path

class RiskChip extends StatelessWidget {
  final String label;
  final double score; // 0..1
  const RiskChip({Key? key, required this.label, required this.score})
      : super(key: key);

  Color _colorForScore() {
    if (score < 0.33) return AppColors.success;
    if (score < 0.66) return AppColors.warn;
    return AppColors.danger;
  }

  @override
  Widget build(BuildContext context) {
    final color = _colorForScore();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.health_and_safety, size: 16, color: color),
          const SizedBox(width: 8),
          Text(label,
              style: TextStyle(color: color, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
