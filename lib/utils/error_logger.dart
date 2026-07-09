import 'dart:io';

import 'package:path_provider/path_provider.dart';

/// Writes error/debug logs to a local file during the test phase.
///
/// Usage:
/// ```dart
/// await ErrorLogger.log('Something went wrong', error: e);
/// ```
///
/// Logs are written to `error_logs/` directory in the app's documents folder.
class ErrorLogger {
  ErrorLogger._();

  static const String _logDirName = 'error_logs';
  static const String _logFileName = 'berry_errors.log';

  static File? _logFile;

  /// Initializes the log file. Call once at app startup.
  static Future<void> init() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final logDir = Directory('${dir.path}/$_logDirName');
      if (!await logDir.exists()) {
        await logDir.create(recursive: true);
      }
      _logFile = File('${logDir.path}/$_logFileName');

      // Write a session header
      final timestamp = DateTime.now().toIso8601String();
      await _logFile!.writeAsString(
        '\n━━━ Session: $timestamp ━━━\n',
        mode: FileMode.append,
      );
    } catch (_) {
      // Silently fail — logging is non-critical in production
    }
  }

  /// Logs a message with optional error and stack trace.
  static Future<void> log(
    String message, {
    Object? error,
    StackTrace? stackTrace,
  }) async {
    final timestamp = DateTime.now().toIso8601String();
    final buffer = StringBuffer()
      ..write('[$timestamp] $message');

    if (error != null) {
      buffer.write('\n  Error: $error');
    }
    if (stackTrace != null) {
      buffer.write('\n  Stack: $stackTrace');
    }
    buffer.writeln();

    // Also print to console during development
    // ignore: avoid_print
    print(buffer.toString());

    try {
      if (_logFile != null) {
        await _logFile!.writeAsString(
          buffer.toString(),
          mode: FileMode.append,
        );
      }
    } catch (_) {
      // ignore: avoid_print
      print('[ErrorLogger] Failed to write to log file');
    }
  }

  /// Returns the path to the log file, or null if not initialized.
  static String? get logFilePath => _logFile?.path;
}
