import 'dart:io';
import 'dart:typed_data';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../editor/editor_screen.dart';
import '../services/ad_manager.dart';
import '../utils/error_logger.dart';

/// Home screen — the entry point for RICHY Lite.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();

  /// Set BEFORE opening the camera/gallery so when the native
  /// activity closes, Flutter renders a loading overlay instead
  /// of flashing the home screen content.
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // Preload the first interstitial ad for this session
    AdManager.loadInterstitial();
  }



  Future<void> _pickFromCamera() async {
    // ── Set loading BEFORE camera opens ───────────────────────
    setState(() => _isLoading = true);

    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 3840,
        maxHeight: 3840,
        imageQuality: 95,
        preferredCameraDevice: CameraDevice.rear,
      );
      if (photo != null) {
        await ErrorLogger.log('Photo captured from camera: ${photo.path}');
        if (mounted) {
          await Navigator.of(context).push<Uint8List>(
            MaterialPageRoute(
              builder: (_) => RichyEditorScreen(imageFile: File(photo.path)),
            ),
          );
        }
      }
    } catch (e, stack) {
      await ErrorLogger.log(
        'Failed to capture photo from camera',
        error: e,
        stackTrace: stack,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('errors.camera_unavailable'.tr()),
            backgroundColor: Colors.red.shade300,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _pickFromGallery() async {
    setState(() => _isLoading = true);

    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 3840,
        maxHeight: 3840,
        imageQuality: 95,
      );
      if (image != null) {
        await ErrorLogger.log('Image picked from gallery: ${image.path}');
        if (mounted) {
          await Navigator.of(context).push<Uint8List>(
            MaterialPageRoute(
              builder: (_) => RichyEditorScreen(imageFile: File(image.path)),
            ),
          );
        }
      }
    } catch (e, stack) {
      await ErrorLogger.log(
        'Failed to pick image from gallery',
        error: e,
        stackTrace: stack,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('errors.gallery_unavailable'.tr()),
            backgroundColor: Colors.red.shade300,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // ── Home content ─────────────────────────────────────
        Scaffold(
          body: SafeArea(
            child: Column(
              children: [
                Align(
                  alignment: Alignment.topRight,
                  child: Padding(
                    padding: const EdgeInsets.only(top: 8.0, right: 8.0),
                    child: IconButton(
                      icon: const Icon(Icons.info_outline, color: Colors.grey),
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: const Text('Privacy Policy'),
                            content: Column(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('RICHY Lite values your privacy. We use device identifiers solely to deliver relevant advertisements.'),
                                const SizedBox(height: 16),
                                InkWell(
                                  onTap: () => launchUrl(Uri.parse('https://richardchung0907.github.io/richy-Lite/')),
                                  child: const Text(
                                    'https://richardchung0907.github.io/richy-Lite/',
                                    style: TextStyle(color: Colors.blue, decoration: TextDecoration.underline),
                                  ),
                                ),
                              ],
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.of(context).pop(),
                                child: const Text('OK'),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Column(
                      children: [
                        const Spacer(flex: 2),
                  Text(
                    'home.title'.tr(),
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                          letterSpacing: 3,
                          color: const Color(0xFFE6395A),
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'home.subtitle'.tr(),
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          letterSpacing: 6,
                          fontWeight: FontWeight.w300,
                        ),
                  ),
                  const Spacer(flex: 1),
                  Container(
                    width: double.infinity,
                    height: 280,
                    decoration: BoxDecoration(
                      color: Colors.white.withAlpha(180),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: const Color(0xFFFFD6E0),
                        width: 2,
                        strokeAlign: BorderSide.strokeAlignInside,
                      ),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(
                          Icons.camera_alt_rounded,
                          size: 72,
                          color: Color(0xFFFFB3C6),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'home.empty_state'.tr(),
                          textAlign: TextAlign.center,
                          style: Theme.of(context)
                              .textTheme
                              .bodyMedium
                              ?.copyWith(
                                color: const Color(0xFF9E9E9E),
                                height: 1.6,
                              ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(flex: 2),
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton.icon(
                      onPressed: _pickFromCamera,
                      icon: const Icon(Icons.camera_alt_rounded, size: 22),
                      label: Text('home.take_photo'.tr()),
                    ),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: OutlinedButton.icon(
                      onPressed: _pickFromGallery,
                      icon: const Icon(Icons.photo_library_rounded, size: 22),
                      label: Text('home.open_gallery'.tr()),
                    ),
                  ),
                        const Spacer(flex: 1),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        // ── Loading overlay (active while camera/gallery is open) ─
        if (_isLoading)
          Container(
            color: const Color(0xFFFFF0F3),
            child: const Center(
              child: CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFE6395A)),
              ),
            ),
          ),
      ],
    );
  }
}
