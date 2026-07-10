import 'dart:io';

import 'package:flutter/material.dart';
import 'package:gal/gal.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pro_image_editor/pro_image_editor.dart';
import 'package:share_plus/share_plus.dart';

import 'custom_filters.dart';
import '../utils/error_logger.dart';

/// Wraps [ProImageEditor] with RICHY Lite's streamlined configuration:
/// - Only Filter + Tune (Brightness/Contrast/Saturation) tools enabled
/// - 5 custom premium color filter presets
/// - Reset button to clear all adjustments
/// - On "Done": captures output bytes and triggers native share sheet
class RichyEditorScreen extends StatelessWidget {
  const RichyEditorScreen({
    super.key,
    required this.imageFile,
  });

  final File imageFile;

  // ── Main Editor Config ─────────────────────────────────────────
  ProImageEditorConfigs _buildConfigs(BuildContext context) {
    return ProImageEditorConfigs(
      // Pink theme to match the app
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF6B8A),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),

      // ── Main Editor: only show Filter + Tune tools ────────────
      mainEditor: MainEditorConfigs(
        tools: const [
          SubEditorMode.filter,
          SubEditorMode.tune,
        ],
      ),

      // ── Filter Editor: 5 custom presets ───────────────────────
      filterEditor: FilterEditorConfigs(
        filterList: RichyFilters.all,
        // enableMultiSelection: false means each new filter replaces
        // the previous one (consumer-friendly single-filter mode)
        enableMultiSelection: false,
      ),

      // ── Tune Editor: only Brightness / Contrast / Saturation ──
      tuneEditor: TuneEditorConfigs(
        tuneAdjustmentOptions: [
          TuneAdjustmentItem(
            id: 'brightness',
            icon: Icons.brightness_6,
            label: 'Brightness',
            min: -0.5,
            max: 0.5,
            divisions: 200,
            labelMultiplier: 200,
            toMatrix: ColorFilterAddons.brightness,
          ),
          TuneAdjustmentItem(
            id: 'contrast',
            icon: Icons.contrast,
            label: 'Contrast',
            min: -0.5,
            max: 0.5,
            divisions: 200,
            labelMultiplier: 200,
            toMatrix: ColorFilterAddons.contrast,
          ),
          TuneAdjustmentItem(
            id: 'saturation',
            icon: Icons.colorize,
            label: 'Saturation',
            min: -0.5,
            max: 0.5,
            divisions: 200,
            labelMultiplier: 200,
            toMatrix: ColorFilterAddons.saturation,
          ),
        ],
      ),

      // Disable unused editors explicitly (belt-and-suspenders)
      paintEditor: const PaintEditorConfigs(),
      textEditor: const TextEditorConfigs(),
      cropRotateEditor: const CropRotateEditorConfigs(),
      blurEditor: const BlurEditorConfigs(),
      emojiEditor: const EmojiEditorConfigs(),
      stickerEditor: const StickerEditorConfigs(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ProImageEditor.file(
      imageFile,
      configs: _buildConfigs(context),
      callbacks: ProImageEditorCallbacks(
        onImageEditingComplete: (bytes) async {
          try {
            await ErrorLogger.log('Editor completed — saving ${bytes.length} bytes');

            // Step 1: Save to gallery (reliable, direct MediaStore write)
            bool saved = false;
            try {
              await Gal.putImageBytes(bytes);
              saved = true;
            } catch (e) {
              await ErrorLogger.log('Gallery save failed', error: e);
            }

            // Step 2: Show confirmation on editor before popping
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(saved
                      ? 'Saved to gallery! Opening share…'
                      : 'Opening share…'),
                  duration: const Duration(seconds: 2),
                  backgroundColor: saved
                      ? const Color(0xFF4CAF50)
                      : const Color(0xFFFF9800),
                ),
              );
              // Brief delay so user sees the SnackBar
              await Future.delayed(const Duration(milliseconds: 800));
              Navigator.of(context).pop();
            }

            // Step 3: Open share sheet from home screen for social sharing
            // (not for Save — that's already handled by gal above)
            try {
              final tempDir = await getTemporaryDirectory();
              final file = File(
                '${tempDir.path}/richy_share_${DateTime.now().millisecondsSinceEpoch}.jpg',
              );
              await file.writeAsBytes(bytes);
              await SharePlus.instance.share(
                ShareParams(files: [XFile(file.path)], subject: 'RICHY Lite'),
              );
            } catch (e) {
              // Share is best-effort
            }

            await ErrorLogger.log(saved ? 'Saved to gallery + shared' : 'Shared only');
          } catch (e, stack) {
            await ErrorLogger.log('Save/share pipeline failed', error: e, stackTrace: stack);
          }
        },
        onCloseEditor: (_) {
          ErrorLogger.log('Editor closed by user');
          // Pop back to home — the editor does NOT auto-pop
          if (context.mounted) {
            Navigator.of(context).pop();
          }
        },
      ),
    );
  }
}
