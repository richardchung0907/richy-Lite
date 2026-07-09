import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../editor/editor_screen.dart';
import '../utils/error_logger.dart';

/// Home screen — the entry point for RICHY Lite.
///
/// Shows a clean minimalist header "RICHY", a large center illustration
/// placeholder, and two primary CTA buttons: Take Photo & Open Gallery.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickFromCamera() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 92,
        preferredCameraDevice: CameraDevice.rear,
      );
      if (photo != null) {
        await ErrorLogger.log('Photo captured from camera: ${photo.path}');
        _navigateToEditor(File(photo.path));
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
    }
  }

  Future<void> _pickFromGallery() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 92,
      );
      if (image != null) {
        await ErrorLogger.log('Image picked from gallery: ${image.path}');
        _navigateToEditor(File(image.path));
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
    }
  }

  void _navigateToEditor(File imageFile) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RichyEditorScreen(imageFile: imageFile),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              const Spacer(flex: 2),

              // ── Header ──────────────────────────────────────
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

              // ── Center Placeholder ──────────────────────────
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
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: const Color(0xFF9E9E9E),
                            height: 1.6,
                          ),
                    ),
                  ],
                ),
              ),

              const Spacer(flex: 2),

              // ── Action Buttons ──────────────────────────────
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
    );
  }
}
