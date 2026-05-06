import 'package:flutter/material.dart';

// Exact same TColors your login.dart already references
abstract class TColors {
  TColors._();

  // Brand — violet + cyan gradient (your login button)
  static const Color primary         = Color(0xFF4A3AB5);
  static const Color secondary       = Color(0xFF00BCD4);

  // Backgrounds
  static const Color lightBackground = Color(0xFFF5F5F5);
  static const Color darkBackground  = Color(0xFF0D1117);
  static const Color surface         = Colors.white;
  static const Color darkSurface     = Color(0xFF161B22);

  // Text
  static const Color textPrimary     = Color(0xFF1A1A2E);
  static const Color textSecondary   = Color(0xFF6B7280);
  static const Color textHint        = Color(0xFFADB5BD);

  // Semantic
  static const Color success         = Color(0xFF10B981);
  static const Color warning         = Color(0xFFF59E0B);
  static const Color error           = Color(0xFFEF4444);
  static const Color info            = Color(0xFF3B82F6);

  // 4 Governance Tier accents (thesis Ch 5.2)
  static const Color strategicTier   = Color(0xFF7C3AED); // Owner/Leader/Admin
  static const Color academicTier    = Color(0xFF2563EB); // Teachers/HoD
  static const Color supportTier     = Color(0xFF0891B2); // HR/IT/Counsellor
  static const Color externalTier    = Color(0xFF059669); // Student/Parent
}