import 'package:flutter/material.dart';

/// BERRY Lite app theme — pastel light-pink minimalist aesthetic.
class BerryTheme {
  BerryTheme._();

  // ── Color Palette ──────────────────────────────────────────────
  static const Color pink50 = Color(0xFFFFF0F3);
  static const Color pink100 = Color(0xFFFFD6E0);
  static const Color pink200 = Color(0xFFFFB3C6);
  static const Color pink300 = Color(0xFFFF8FA8);
  static const Color pink400 = Color(0xFFFF6B8A);
  static const Color pink500 = Color(0xFFFF4770);
  static const Color pink600 = Color(0xFFE6395A);

  static const Color darkText = Color(0xFF2D2D2D);
  static const Color mediumText = Color(0xFF6B6B6B);
  static const Color lightText = Color(0xFF9E9E9E);

  static const Color surfaceWhite = Color(0xFFFFFBFD);
  static const Color cardWhite = Colors.white;

  // ── Theme Data ─────────────────────────────────────────────────
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: const ColorScheme.light(
        primary: pink500,
        onPrimary: Colors.white,
        secondary: pink300,
        surface: surfaceWhite,
        onSurface: darkText,
      ),
      scaffoldBackgroundColor: pink50,

      // AppBar
      appBarTheme: const AppBarTheme(
        backgroundColor: pink50,
        foregroundColor: darkText,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: darkText,
          fontSize: 22,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.2,
        ),
      ),

      // Elevated Buttons (primary CTA)
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: pink400,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      // Outlined Buttons (secondary)
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: pink500,
          side: const BorderSide(color: pink300, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      // Cards
      cardTheme: CardThemeData(
        color: cardWhite,
        elevation: 2,
        shadowColor: pink100.withAlpha(100),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),

      // Text
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          color: darkText,
          fontSize: 32,
          fontWeight: FontWeight.w700,
        ),
        headlineMedium: TextStyle(
          color: darkText,
          fontSize: 24,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: TextStyle(
          color: darkText,
          fontSize: 16,
          fontWeight: FontWeight.w400,
        ),
        bodyMedium: TextStyle(
          color: mediumText,
          fontSize: 14,
          fontWeight: FontWeight.w400,
        ),
        labelLarge: TextStyle(
          color: darkText,
          fontSize: 14,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
