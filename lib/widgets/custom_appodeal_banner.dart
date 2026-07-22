import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:stack_appodeal_flutter/stack_appodeal_flutter.dart';
import 'package:device_info_plus/device_info_plus.dart';

class CustomAppodealBanner extends StatefulWidget {
  /// The size of the banner to display.
  final AppodealBannerSize adSize;

  /// The placement identifier for the banner ad.
  /// Defaults to "default".
  final String placement;

  const CustomAppodealBanner({
    super.key,
    required this.adSize,
    this.placement = "default",
  });

  @override
  _CustomAppodealBannerState createState() => _CustomAppodealBannerState();
}

class BannerConfig {
  final Size size;
  final bool isEmulator;

  BannerConfig({required this.size, required this.isEmulator});
}

class _CustomAppodealBannerState extends State<CustomAppodealBanner> {
  final UniqueKey _key = UniqueKey();
  final String _viewType = 'appodeal_flutter/banner_view';

  late final Future<BannerConfig> _bannerConfigFuture;

  @override
  void initState() {
    super.initState();
    _bannerConfigFuture = _getBannerConfig();
  }

  Future<BannerConfig> _getBannerConfig() async {
    final size = Size(
      widget.adSize.width.toDouble(),
      widget.adSize.height.toDouble(),
    );
    bool isEmulator = false;
    try {
      if (Platform.isAndroid) {
        final androidInfo = await DeviceInfoPlugin().androidInfo;
        // isPhysicalDevice will be false on Android Emulators
        isEmulator = !androidInfo.isPhysicalDevice;
      }
    } catch (e) {
      // In case of any exception, default to false (safe-fallback)
    }
    return BannerConfig(size: size, isEmulator: isEmulator);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<BannerConfig>(
      future: _bannerConfigFuture,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const SizedBox.shrink();
        }
        final config = snapshot.data!;
        return SizedBox.fromSize(
          size: config.size,
          child: _buildPlatformSpecificView(config.isEmulator),
        );
      },
    );
  }

  /// Builds the platform-specific view for displaying the banner.
  Widget _buildPlatformSpecificView(bool isEmulator) {
    if (Platform.isIOS) {
      return UiKitView(
        key: _key,
        viewType: _viewType,
        creationParams: _bannerCreationParams,
        creationParamsCodec: const StandardMessageCodec(),
      );
    } else if (Platform.isAndroid) {
      // We dynamically adapt composition modes:
      // 1. On real physical Android devices (especially with GPUs like Mali on Samsung A5),
      //    we use Hybrid Composition (initExpensiveAndroidView) to resolve texture composting/transparency bugs.
      // 2. On Android Emulators (running swiftshader/translation layers), Hybrid Composition
      //    deadlocks or freezes into a black screen after focus switches (such as native Share sheet popups).
      //    Thus, we use standard Virtual Display (initSurfaceAndroidView) on emulators.
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
          if (isEmulator) {
            // Fallback to Virtual Display for Emulators
            return PlatformViewsService.initSurfaceAndroidView(
              id: params.id,
              viewType: _viewType,
              layoutDirection: TextDirection.ltr,
              creationParams: _bannerCreationParams,
              creationParamsCodec: const StandardMessageCodec(),
              onFocus: () => params.onFocusChanged(true),
            )
              ..addOnPlatformViewCreatedListener(params.onPlatformViewCreated)
              ..create();
          } else {
            // Keep Hybrid Composition for physical devices
            return PlatformViewsService.initExpensiveAndroidView(
              id: params.id,
              viewType: _viewType,
              layoutDirection: TextDirection.ltr,
              creationParams: _bannerCreationParams,
              creationParamsCodec: const StandardMessageCodec(),
              onFocus: () => params.onFocusChanged(true),
            )
              ..addOnPlatformViewCreatedListener(params.onPlatformViewCreated)
              ..create();
          }
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