import 'dart:io';

import 'package:flutter/material.dart';
import 'package:pro_image_editor/pro_image_editor.dart';

import '../utils/error_logger.dart';
import 'custom_filters.dart';

/// Wraps [ProImageEditor] with RICHY Lite's streamlined configuration:
/// - Only Filter + Tune tools enabled
/// - 5 custom premium color filter presets
/// - Anti-double-pop guard prevents navigator stack corruption
class RichyEditorScreen extends StatefulWidget {
  const RichyEditorScreen({
    super.key,
    required this.imageFile,
  });

  final File imageFile;

  @override
  State<RichyEditorScreen> createState() => _RichyEditorScreenState();
}

class _RichyEditorScreenState extends State<RichyEditorScreen> {
  /// Prevents double-pop when the tick button fires twice
  /// (e.g. rapid double-tap or pro_image_editor internal re-fire)
  bool _isFinishing = false;

  /// Created ONCE and reused across all rebuilds.
  /// Prevents slider value drift and filter layering bugs caused by
  /// new object references on every `build()` call.
  late final ProImageEditorConfigs _editorConfigs = ProImageEditorConfigs(
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFFFF6B8A),
        brightness: Brightness.dark,
      ),
      useMaterial3: true,
    ),
    mainEditor: const MainEditorConfigs(
      tools: [
        SubEditorMode.filter,
        SubEditorMode.tune,
      ],
    ),
    filterEditor: FilterEditorConfigs(
      filterList: RichyFilters.all,
      enableMultiSelection: false,
    ),
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
    paintEditor: const PaintEditorConfigs(),
    textEditor: const TextEditorConfigs(),
    cropRotateEditor: const CropRotateEditorConfigs(),
    blurEditor: const BlurEditorConfigs(),
    emojiEditor: const EmojiEditorConfigs(),
    stickerEditor: const StickerEditorConfigs(),
  );

  @override
  Widget build(BuildContext context) {
    return ProImageEditor.file(
      widget.imageFile,
      configs: _editorConfigs,
      callbacks: ProImageEditorCallbacks(
        onImageEditingComplete: (bytes) async {
          if (_isFinishing) return;
          _isFinishing = true;

          await ErrorLogger.log('Editor completed — ${bytes.length} bytes');
          if (mounted) {
            Navigator.of(context).pop(bytes);
          }
        },
        onCloseEditor: (_) {
          if (_isFinishing) return;
          _isFinishing = true;

          ErrorLogger.log('Editor closed by user');
          if (mounted) {
            Navigator.of(context).pop();
          }
        },
      ),
    );
  }
}
