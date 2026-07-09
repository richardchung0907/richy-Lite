import 'dart:io';

import 'package:flutter/material.dart';
import 'package:pro_image_editor/pro_image_editor.dart';

import 'custom_filters.dart';
import '../services/share_service.dart';
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
          // Pop immediately so the "Changes are being applied" loading
          // dialog closes — the user returns to home instantly.
          if (context.mounted) {
            Navigator.of(context).pop();
          }
          // Save to gallery + share in background
          try {
            await ErrorLogger.log('Editor completed — saving ${bytes.length} bytes');
            final saved = await ShareService.saveAndShare(bytes);
            await ErrorLogger.log(
              saved ? 'Saved to gallery + shared' : 'Shared (gallery save skipped)',
            );
          } catch (e, stack) {
            await ErrorLogger.log(
              'Save/share pipeline failed',
              error: e,
              stackTrace: stack,
            );
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
