import 'dart:io';
import 'dart:typed_data';

import 'package:share_plus/share_plus.dart';

/// Wraps share_plus to provide a clean one-click share API.
///
/// The share sheet natively targets Instagram, Facebook, Threads,
/// X (Twitter), WhatsApp, and any other app that accepts images.
class ShareService {
  ShareService._();

  /// Shares image bytes via the native OS share sheet.
  ///
  /// Writes bytes to a temporary file so share_plus can attach it.
  static Future<void> shareImageBytes(Uint8List bytes) async {
    final tempDir = Directory.systemTemp;
    final file = File('${tempDir.path}/richy_share_${DateTime.now().millisecondsSinceEpoch}.jpg');
    await file.writeAsBytes(bytes);

    await SharePlus.instance.share(
      ShareParams(
        files: [XFile(file.path)],
        subject: 'RICHY Lite',
      ),
    );
  }

  /// Shares a file path directly via the native OS share sheet.
  static Future<void> shareFile(File file) async {
    await SharePlus.instance.share(
      ShareParams(
        files: [XFile(file.path)],
        subject: 'RICHY Lite',
      ),
    );
  }
}
