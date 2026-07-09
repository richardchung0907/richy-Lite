import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'screens/home_screen.dart';
import 'theme/app_theme.dart';
import 'utils/error_logger.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize i18n
  await EasyLocalization.ensureInitialized();

  // Initialize error logger for test phase
  await ErrorLogger.init();
  await ErrorLogger.log('App starting — RICHY Lite v1.0.0');

  runApp(
    EasyLocalization(
      supportedLocales: const [Locale('en')],
      path: 'assets/translations',
      fallbackLocale: const Locale('en'),
      startLocale: const Locale('en'),
      child: const RichyApp(),
    ),
  );
}

class RichyApp extends StatelessWidget {
  const RichyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RICHY Lite',
      debugShowCheckedModeBanner: false,
      theme: RichyTheme.lightTheme,

      // EasyLocalization delegates
      localizationsDelegates: const [
        ...context.localizationDelegates,
        GlobalMaterialLocalization.delegate,
        GlobalWidgetsLocalization.delegate,
        GlobalCupertinoLocalization.delegate,
      ],
      supportedLocales: context.supportedLocales,
      locale: context.locale,

      home: const HomeScreen(),
    );
  }
}
