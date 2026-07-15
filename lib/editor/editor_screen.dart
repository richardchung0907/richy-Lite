import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:pro_image_editor/pro_image_editor.dart';

import '../services/ad_manager.dart';
import '../services/share_service.dart';
import '../utils/error_logger.dart';
import 'custom_filters.dart';

/// Wraps [ProImageEditor] with RICHY Lite's streamlined configuration:
/// - Only Filter + Tune tools enabled
/// - 5 custom premium color filter presets
/// - Anti-double-pop guard prevents navigator stack corruption
/// - Custom top app bar with explicit Save and Share buttons
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

  /// Tracks the history pointer at the time of the last successful save.
  /// If the current history pointer matches this value, we can safely close
  /// the editor without showing the "unsaved changes" warning.
  int _lastSavedHistoryPointer = 0;
  
  /// Tracks the history length at the time of the last successful save.
  /// This ensures that if a user undoes to a saved pointer but has unsaved
  /// redo history, they still get a warning before losing that redo history.
  int _lastSavedHistoryLength = 1;

  void _showSuccessToast(String message) {
    if (!mounted) return;

    final overlay = Overlay.of(context);
    late OverlayEntry overlayEntry;
    bool isRemoved = false;

    void removeToast() {
      if (!isRemoved) {
        isRemoved = true;
        try {
          overlayEntry.remove();
        } catch (_) {}
      }
    }

    overlayEntry = OverlayEntry(
      builder: (_) => Stack(
        children: [
          Positioned.fill(
            child: const ModalBarrier(
              color: Colors.transparent,
              dismissible: false,
            ),
          ),
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            left: 24,
            right: 24,
            child: Material(
              color: Colors.transparent,
              child: Dismissible(
                key: UniqueKey(),
                direction: DismissDirection.horizontal,
                onDismissed: (_) => removeToast(),
                child: GestureDetector(
                  onTap: removeToast,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE6395A),
                      borderRadius: BorderRadius.circular(30),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withAlpha(38),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          message,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );

    overlay.insert(overlayEntry);

    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        removeToast();
      }
    });
  }

  void _showLoading(BuildContext context) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(
        child: CircularProgressIndicator(color: Color(0xFFFF6B8A)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Fresh config each build — lets pro_image_editor
    // correctly reinitialize sub-editor state on re-entry
    final editorConfigs = ProImageEditorConfigs(
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF6B8A),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      mainEditor: MainEditorConfigs(
        widgets: MainEditorWidgets(
          appBar: (editor, rebuildStream) => ReactiveAppbar(
            stream: rebuildStream,
            builder: (_) => AppBar(
              backgroundColor: Colors.transparent,
              elevation: 0,
              leading: IconButton(
                icon: const Icon(Icons.close, color: Colors.white),
                onPressed: () {
                  final currentPointer = editor.stateManager.historyPointer;
                  final currentLength = editor.stateManager.stateHistory.length;

                  if (currentPointer == _lastSavedHistoryPointer && 
                      currentLength == _lastSavedHistoryLength) {
                    if (mounted) Navigator.of(context).pop();
                  } else {
                    editor.closeWarning();
                  }
                },
              ),
              actions: [
                IconButton(
                  icon: Icon(
                    Icons.undo,
                    color: editor.canUndo ? Colors.white : Colors.white.withAlpha(80),
                  ),
                  onPressed: editor.canUndo ? () => editor.undoAction() : null,
                ),
                IconButton(
                  icon: Icon(
                    Icons.redo,
                    color: editor.canRedo ? Colors.white : Colors.white.withAlpha(80),
                  ),
                  onPressed: editor.canRedo ? () => editor.redoAction() : null,
                ),
                TextButton(
                  onPressed: () async {
                    if (_isFinishing) return;
                    _isFinishing = true;

                    _showLoading(context);
                    Uint8List? bytes;
                    try {
                      bytes = await editor.captureEditorImage();
                      if (mounted) Navigator.of(context).pop(); // hide loading
                    } catch (_) {
                      if (mounted) Navigator.of(context).pop();
                    }

                    if (bytes != null && mounted) {
                      bool isDialogShowing = false;
                      if (mounted) {
                        _showLoading(context);
                        isDialogShowing = true;
                      }
                      
                      final isSaved = await ShareService.saveImage(bytes);
                      
                      if (mounted && isDialogShowing) {
                        Navigator.of(context).pop(); // hide loading
                      }

                      if (isSaved && mounted) {
                        setState(() {
                          _lastSavedHistoryPointer = editor.stateManager.historyPointer;
                          _lastSavedHistoryLength = editor.stateManager.stateHistory.length;
                        });
                        _showSuccessToast('✨ Photo saved to gallery!');
                        Future.delayed(const Duration(milliseconds: 500), () {
                          AdManager.showInterstitial();
                        });
                      }
                    }
                    _isFinishing = false;
                  },
                  child: const Text('Save', style: TextStyle(color: Colors.white, fontSize: 16)),
                ),
                TextButton(
                  onPressed: () async {
                    if (_isFinishing) return;
                    _isFinishing = true;

                    _showLoading(context);
                    Uint8List? bytes;
                    try {
                      bytes = await editor.captureEditorImage();
                      if (mounted) Navigator.of(context).pop(); // hide loading
                    } catch (_) {
                      if (mounted) Navigator.of(context).pop();
                    }

                    if (bytes != null && mounted) {
                      bool isDialogShowing = false;
                      if (mounted) {
                        _showLoading(context);
                        isDialogShowing = true;
                      }
                      
                      await ShareService.shareImage(bytes, context: context);
                      
                      if (mounted && isDialogShowing) {
                        Navigator.of(context).pop(); // hide loading
                      }
                      
                      AdManager.showInterstitial();
                    }
                    _isFinishing = false;
                  },
                  child: const Text('Share', style: TextStyle(color: Colors.white, fontSize: 16)),
                ),
              ],
            ),
          ),
        ),
        tools: const [
          SubEditorMode.filter,
          SubEditorMode.tune,
        ],
        enableSubEditorPage: false,
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

    return Column(
      children: [
        Expanded(
          child: ProImageEditor.file(
            widget.imageFile,
            configs: editorConfigs,
            callbacks: ProImageEditorCallbacks(
              onCloseEditor: (_) {
                if (_isFinishing) return;

                ErrorLogger.log('Editor closed by user');
                if (mounted) {
                  Navigator.of(context).pop();
                }
              },
            ),
          ),
        ),
        const SafeArea(
          top: false,
          child: AdBannerWidget(),
        ),
      ],
    );
  }
}
