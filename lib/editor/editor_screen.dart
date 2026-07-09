import 'dart:io';

import 'package:flutter/material.dart';
import 'package:pro_image_editor/pro_image_editor.dart';

import 'custom_filters.dart';
import '../services/share_service.dart';
import '../utils/error_logger.dart';

/// Wraps [ProImageEditor] with BERRY Lite's streamlined configuration:
/// - Only Filter + Tune (Brightness/Contrast/Saturation) tools enabled
/// - 5 custom premium color filter presets
/// - Reset button to clear all adjustments
/// - On "Done": captures output bytes and triggers native share sheet
class BerryEditorScreen extends StatelessWidget {
  const BerryEditorScreen({
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
        filterList: BerryFilters.all,
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
            icon: Icons.saturation,
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
          await ErrorLogger.log('Editor completed — sharing ${bytes.length} bytes');
          await ShareService.shareImageBytes(bytes);
          // Pop back to home after share sheet
          if (context.mounted) {
            Navigator.of(context).popUntil((route) => route.isFirst);
          }
        },
        onCloseButtonPressed: () {
          ErrorLogger.log('Editor closed by user');
          Navigator.of(context).pop();
        },
      ),
    );
  }
}
