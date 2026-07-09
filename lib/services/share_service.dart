import 'dart:io';
import 'dart:typed_data';

import 'package:gal/gal.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

/// Handles both gallery save and social share for image output.
///
/// - Saves directly to device gallery (bypasses unreliable share-sheet Save)
/// - Opens native share sheet for social media posting
class ShareService {
  ShareService._();

  /// Saves image to gallery, then opens share sheet.
  ///
  /// Gallery save uses `gal` package which works on Android 10+ / iOS
  /// without requiring WRITE_EXTERNAL_STORAGE permission.
  ///
  /// Returns true if at least one operation succeeded.
  static Future<bool> saveAndShare(Uint8List bytes) async {
    bool saved = false;
    String? savedPath;

    // Step 1: Save to device gallery
    try {
      await Gal.putImageBytes(bytes);
      saved = true;
    } catch (e) {
      // Gallery save is best-effort — log and continue to share
    }

    // Step 2: Open share sheet
    try {
      final tempDir = await getTemporaryDirectory();
      final file = File(
        '${tempDir.path}/richy_share_${DateTime.now().millisecondsSinceEpoch}.jpg',
      );
      await file.writeAsBytes(bytes);

      await SharePlus.instance.share(
        ShareParams(
          files: [XFile(file.path)],
          subject: 'RICHY Lite',
        ),
      );
      // Don't delete temp file — share target may still be reading it
    } catch (e) {
      // Share is best-effort
    }

    return saved;
  }
}
