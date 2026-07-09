import 'dart:io';
import 'dart:typed_data';

import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

/// Wraps share_plus to provide a clean one-click share API.
///
/// The share sheet natively targets Instagram, Facebook, Threads,
/// X (Twitter), WhatsApp, and any other app that accepts images.
class ShareService {
  ShareService._();

  /// Shares image bytes via the native OS share sheet.
  ///
  /// Writes bytes to the app's temporary directory so share_plus can attach it.
  /// Returns true if share was successful or user dismissed, false on error.
  static Future<bool> shareImageBytes(Uint8List bytes) async {
    try {
      final tempDir = await getTemporaryDirectory();
      final file = File(
        '${tempDir.path}/richy_share_${DateTime.now().millisecondsSinceEpoch}.jpg',
      );
      await file.writeAsBytes(bytes);

      final result = await SharePlus.instance.share(
        ShareParams(
          files: [XFile(file.path)],
          subject: 'RICHY Lite',
        ),
      );

      // Note: do NOT delete the temp file — the share target
      // (e.g., "Save") may still be reading it asynchronously.
      // The OS cleans up the temp directory periodically.

      return result.status == ShareResultStatus.success ||
          result.status == ShareResultStatus.dismissed;
    } catch (e) {
      return false;
    }
  }

  /// Shares a file path directly via the native OS share sheet.
  static Future<bool> shareFile(File file) async {
    try {
      final result = await SharePlus.instance.share(
        ShareParams(
          files: [XFile(file.path)],
          subject: 'RICHY Lite',
        ),
      );
      return result.status == ShareResultStatus.success ||
          result.status == ShareResultStatus.dismissed;
    } catch (e) {
      return false;
    }
  }
}
