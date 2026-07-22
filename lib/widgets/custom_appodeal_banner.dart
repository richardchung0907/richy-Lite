import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:stack_appodeal_flutter/stack_appodeal_flutter.dart';
import '../services/ad_manager.dart';

/// A custom AppodealBanner widget that implements custom safe-sizing and 
/// forces standard Hybrid Composition on Android to fix transparency and
/// visibility-clipping bugs on older device pixel ratio devices.
class CustomAppodealBanner extends StatefulWidget {
  /// The size of the banner to display.
  final AppodealBannerSize adSize;

  /// The placement identifier for the banner ad.
  final String placement;

  const CustomAppodealBanner({
    super.key,
    required this.adSize,
    this.placement = "default",
  });

  @override
  State<CustomAppodealBanner> createState() => _CustomAppodealBannerState();
}

class _CustomAppodealBannerState extends State<CustomAppodealBanner> with SingleTickerProviderStateMixin {
  final UniqueKey _key = UniqueKey();
  final String _viewType = 'appodeal_flutter/banner_view';
  late AnimationController _shimmerController;

  @override
  void initState() {
    super.initState();
    _shimmerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _shimmerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // 1. Get the device's device pixel ratio (DPR)
    final dpr = MediaQuery.of(context).devicePixelRatio;
    final double rawHeight = widget.adSize.height.toDouble();

    // 2. Perform the exact safe physical pixel aligned height calculation.
    //    We round up the physical pixel height (ceil) and add 2 safe physical pixels 
    //    to guarantee the ad is NEVER clipped even by a micro-fraction of a pixel.
    //    Finally, divide back by the DPR to get the logical widget height.
    final double safeHeight = ((rawHeight * dpr).ceil() + 2) / dpr;
    final double width = widget.adSize.width.toDouble();

    // 3. Size our custom Appodeal banner to the exact safe-height bounds.
    return SizedBox(
      width: width,
      height: safeHeight,
      child: ValueListenableBuilder<bool>(
        valueListenable: AdManager.isBannerLoadedNotifier,
        builder: (context, isLoaded, child) {
          return Stack(
            children: [
              // 1. Native Appodeal Banner View (Loads silently in the background)
              _buildPlatformSpecificView(),

              // 2. Elegant rosy shimmer overlay (Shown only if not loaded yet)
              if (!isLoaded)
                FadeTransition(
                  opacity: Tween<double>(begin: 0.35, end: 0.95).animate(
                    CurvedAnimation(
                      parent: _shimmerController,
                      curve: Curves.easeInOut,
                    ),
                  ),
                  child: Container(
                    width: width,
                    height: safeHeight,
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          Color(0xFFFFECEF), // Rosy pale pink
                          Color(0xFFFFF5F7), // Extra light pink
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: const Center(
                      child: Text(
                        "L O A D I N G . . .",
                        style: TextStyle(
                          fontSize: 10,
                          color: Color(0xFFFF9EAF),
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2.0,
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  /// Builds the platform-specific view for displaying the banner.
  Widget _buildPlatformSpecificView() {
    if (Platform.isIOS) {
      return UiKitView(
        key: _key,
        viewType: _viewType,
        creationParams: _bannerCreationParams,
        creationParamsCodec: const StandardMessageCodec(),
      );
    } else if (Platform.isAndroid) {
      // Revert to Hybrid Composition (initExpensiveAndroidView) to satisfy Appodeal/AdMob's 
      // strict native VisibilityTracker, ensuring ads load and display with 100% visibility score.
      return PlatformViewLink(
        key: _key,
        viewType: _viewType,
        surfaceFactory: (context, controller) {
          return AndroidViewSurface(
            controller: controller as AndroidViewController,
            gestureRecognizers: const <Factory<OneSequenceGestureRecognizer>>{},
            hitTestBehavior: PlatformViewHitTestBehavior.opaque,
          );
        },
        onCreatePlatformView: (params) {
          return PlatformViewsService.initExpensiveAndroidView(
            id: params.id,
            viewType: _viewType,
            layoutDirection: TextDirection.ltr,
            creationParams: _bannerCreationParams,
            creationParamsCodec: const StandardMessageCodec(),
            onFocus: () {
              params.onFocusChanged(true);
            },
          )
            ..addOnPlatformViewCreatedListener(params.onPlatformViewCreated)
            ..create();
        },
      );
    } else {
      return const SizedBox.shrink(); // Fallback for other platforms
    }
  }

  /// The parameters to pass to the native banner view.
  Map<String, dynamic> get _bannerCreationParams => {
        'adSize': widget.adSize.toMap,
        'placement': widget.placement,
      };
}
