import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'theme_colors.dart';

abstract class AppTheme {
  AppTheme._();

  static ThemeData get lightTheme => ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: ColorScheme.fromSeed(
      seedColor: TColors.primary,
      brightness: Brightness.light,
    ).copyWith(primary: TColors.primary, secondary: TColors.secondary),
    scaffoldBackgroundColor: TColors.lightBackground,
    textTheme: GoogleFonts.poppinsTextTheme().apply(
      bodyColor: TColors.textPrimary,
      displayColor: TColors.textPrimary,
    ),
    inputDecorationTheme: _inputTheme(Brightness.light),
    appBarTheme: const AppBarTheme(
      elevation: 0, centerTitle: true,
      backgroundColor: Colors.transparent,
      foregroundColor: TColors.textPrimary,
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
  );

  static ThemeData get darkTheme => ThemeData(
    useMaterial3: true, brightness: Brightness.dark,
    colorScheme: ColorScheme.fromSeed(
      seedColor: TColors.primary, brightness: Brightness.dark,
    ).copyWith(primary: TColors.primary, secondary: TColors.secondary),
    scaffoldBackgroundColor: TColors.darkBackground,
    textTheme: GoogleFonts.poppinsTextTheme().apply(
      bodyColor: Colors.white, displayColor: Colors.white,
    ),
    inputDecorationTheme: _inputTheme(Brightness.dark),
  );

  static InputDecorationTheme _inputTheme(Brightness b) {
    final d = b == Brightness.dark;
    return InputDecorationTheme(
      filled: true,
      fillColor: d
          ? Colors.white.withOpacity(0.07)
          : Colors.grey.withOpacity(0.07),
      border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none),
      enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(
              color: d
                  ? Colors.white.withOpacity(0.1)
                  : Colors.grey.withOpacity(0.15))),
      focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: TColors.primary, width: 1.5)),
      hintStyle: TextStyle(
          color: d ? Colors.white38 : TColors.textHint, fontSize: 14),
      contentPadding:
      const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
    );
  }
}