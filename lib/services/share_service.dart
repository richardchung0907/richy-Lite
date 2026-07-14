import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:gal/gal.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

/// Unified save + share pipeline for RICHY Lite output images.
///
/// - Saves to device gallery via `gal` (MediaStore, no extra permissions)
/// - Opens native share sheet via `share_plus` for social sharing
/// - Handles iPad `sharePositionOrigin` to prevent crashes
class ShareService {
  ShareService._();

  /// Save image bytes to gallery.
  ///
  /// Returns `true` if gallery save succeeded.
  static Future<bool> saveImage(Uint8List bytes) async {
    try {
      await Gal.putImageBytes(bytes);
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Open the system share sheet for the given image bytes.
  ///
  /// [context] is optional but should be provided on iPad to supply the
  /// `sharePositionOrigin` anchor (prevents a hard crash on iPadOS).
  static Future<void> shareImage(
    Uint8List bytes, {
    BuildContext? context,
  }) async {
    try {
      final tempDir = await getTemporaryDirectory();
      final file = File(
        '${tempDir.path}/richy_share_${DateTime.now().millisecondsSinceEpoch}.jpg',
      );
      await file.writeAsBytes(bytes);

      Rect? anchor;
      if (context != null) {
        try {
          final box = context.findRenderObject() as RenderBox?;
          if (box != null && box.hasSize) {
            anchor = box.localToGlobal(Offset.zero) & box.size;
          }
        } catch (_) {}
      }

      await SharePlus.instance.share(
        ShareParams(
          files: [XFile(file.path)],
          subject: 'RICHY Lite',
          sharePositionOrigin: anchor,
        ),
      );
    } catch (_) {
      // Best-effort
    }
  }
}
