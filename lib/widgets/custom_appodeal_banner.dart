import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:stack_appodeal_flutter/stack_appodeal_flutter.dart';

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

class _CustomAppodealBannerState extends State<CustomAppodealBanner> {
  final UniqueKey _key = UniqueKey();
  final String _viewType = 'appodeal_flutter/banner_view';

  late final Future<Size> _adSizeFuture;

  @override
  void initState() {
    super.initState();
    _adSizeFuture = _getAdSize();
  }

  Future<Size> _getAdSize() async {
    return Size(
      widget.adSize.width.toDouble(),
      widget.adSize.height.toDouble(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Size>(
      future: _adSizeFuture,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const SizedBox.shrink();
        }
        final adSize = snapshot.data!;
        return SizedBox.fromSize(
          size: adSize,
          child: _buildPlatformSpecificView(),
        );
      },
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
      // We force standard Hybrid Composition (using initExpensiveAndroidView) on Android.
      // This embeds the native AdView directly in the real Android view hierarchy.
      // This completely resolves texture composting / transparency bugs on Mali GPUs (e.g. Samsung A5),
      // and guarantees that the Appodeal / Google Mobile Ads visibility monitor reports 100% visibility.
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
            onFocus: () => params.onFocusChanged(true),
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