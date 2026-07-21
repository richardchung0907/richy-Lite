import 'dart:async';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:stack_appodeal_flutter/stack_appodeal_flutter.dart';

/// Manages Appodeal Interstitial and Banner ads for RICHY Lite.
///
/// Uses Appodeal's official SDK with test mode enabled during development
/// to prevent account suspension.
class AdManager {
  AdManager._();

  static const String _androidAppKey = '1e61cf1304d32d47bbbe6c7f6f230eb445645aca570c8414';
  static const String _iosAppKey = ''; // No iOS key in keys.txt for now

  static String get _appKey {
    return Platform.isAndroid ? _androidAppKey : _iosAppKey;
  }

  static bool _isLoading = false;
  static Completer<bool>? _dismissCompleter;
  
  static final Completer<void> _initCompleter = Completer<void>();

  /// Notifier to trigger banner widget rebuilds when a full-screen event closes or dismisses.
  static final ValueNotifier<int> bannerRebuildNotifier = ValueNotifier<int>(0);

  /// Initialize the Appodeal Ads SDK. Call once in `main()`.
  /// Returns immediately, starting initialization in the background.
  static Future<void> init() async {
    _initializeAsync();
  }

  static Future<void> _initializeAsync() async {
    try {
      debugPrint('Appodeal: Initializing SDK...');
      
      // Step 1: Set testing mode (Test ads)
      // Pass true to enable test mode, false to disable it
      await Appodeal.setTesting(true);

      // Disable auto caching for Interstitials to give us manual caching control
      await Appodeal.setAutoCache(AppodealAdType.Interstitial, false);

      // Step 2: Initialize Appodeal SDK
      final key = _appKey;
      if (key.isEmpty) {
        debugPrint('Appodeal: No App Key defined for this platform.');
        if (!_initCompleter.isCompleted) {
          _initCompleter.complete();
        }
        return;
      }

      await Appodeal.initialize(
        appKey: key,
        adTypes: [
          AppodealAdType.Interstitial,
          AppodealAdType.Banner,
        ],
        onInitializationFinished: (errors) {
          if (errors != null && errors.isNotEmpty) {
            debugPrint('Appodeal initialization finished with errors: $errors');
          } else {
            debugPrint('Appodeal initialization finished successfully!');
          }
        },
      );

      // Setup callbacks for Interstitials
      _setupCallbacks();
    } catch (e) {
      debugPrint('Appodeal init error: $e');
    } finally {
      if (!_initCompleter.isCompleted) {
        _initCompleter.complete();
      }
    }
  }

  static void _setupCallbacks() {
    Appodeal.setInterstitialCallbacks(
      onInterstitialLoaded: (isPrecache) {
        debugPrint('Appodeal Interstitial loaded (isPrecache: $isPrecache)');
        _isLoading = false;
      },
      onInterstitialFailedToLoad: () {
        debugPrint('Appodeal Interstitial failed to load');
        _isLoading = false;
        _completeDismiss(false);
      },
      onInterstitialShown: () {
        debugPrint('Appodeal Interstitial shown');
      },
      onInterstitialShowFailed: () {
        debugPrint('Appodeal Interstitial show failed');
        _completeDismiss(false);
        // Force recreation of banners after full screen overlay closes/fails
        bannerRebuildNotifier.value++;
        loadInterstitial(); // Reload in background
      },
      onInterstitialClicked: () {
        debugPrint('Appodeal Interstitial clicked');
      },
      onInterstitialClosed: () {
        debugPrint('Appodeal Interstitial closed by user');
        _completeDismiss(true);
        // Force recreation of banners after full screen overlay closes/fails
        bannerRebuildNotifier.value++;
        loadInterstitial(); // Reload in background
      },
      onInterstitialExpired: () {
        debugPrint('Appodeal Interstitial expired');
        loadInterstitial(); // Reload in background
      },
    );
  }

  /// Preload an interstitial ad.
  static Future<void> loadInterstitial() async {
    await _initCompleter.future;

    if (_isLoading) return;

    final isLoaded = await Appodeal.isLoaded(AppodealAdType.Interstitial);
    if (isLoaded) {
      debugPrint('Appodeal Interstitial is already loaded.');
      return;
    }

    debugPrint('Appodeal: Caching interstitial ad...');
    _isLoading = true;
    try {
      await Appodeal.cache(AppodealAdType.Interstitial);
    } catch (e) {
      debugPrint('Appodeal manual cache error: $e');
      _isLoading = false;
    }
  }

  /// Show the interstitial ad and **wait until the user dismisses it**.
  ///
  /// Returns `true` if the ad was shown AND user dismissed it normally.
  /// Returns `false` if no ad was available, failed to show, or other issues.
  static Future<bool> showInterstitial() async {
    await _initCompleter.future;

    final isLoaded = await Appodeal.isLoaded(AppodealAdType.Interstitial);
    if (!isLoaded) {
      debugPrint('Appodeal Interstitial is not loaded yet.');
      loadInterstitial(); // Trigger cache loading in background
      return false;
    }

    _dismissCompleter = Completer<bool>();

    try {
      await Appodeal.show(AppodealAdType.Interstitial);
      return await _dismissCompleter!.future;
    } catch (e) {
      debugPrint('Appodeal show error: $e');
      _completeDismiss(false);
      loadInterstitial();
      return false;
    }
  }

  static void _completeDismiss(bool value) {
    if (_dismissCompleter != null && !_dismissCompleter!.isCompleted) {
      _dismissCompleter!.complete(value);
    }
    _dismissCompleter = null;
  }

  /// Dispose resources. Call when app is shutting down.
  static void dispose() {
    _dismissCompleter = null;
    _isLoading = false;
  }
}

/// A wrapper widget that displays an AppodealBanner.
///
/// Listens to [AdManager.bannerRebuildNotifier] to automatically recreate the platform view
/// with a unique key whenever full-screen interstitial ads close or fail to show.
/// This prevents the native banner platform view from disappearing after overlay events.
class AdBannerWidget extends StatelessWidget {
  const AdBannerWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<int>(
      valueListenable: AdManager.bannerRebuildNotifier,
      builder: (context, value, child) {
        return Container(
          alignment: Alignment.center,
          color: Colors.transparent,
          child: AppodealBanner(
            key: ValueKey('appodeal_banner_$value'),
            adSize: AppodealBannerSize.BANNER,
            placement: 'default',
          ),
        );
      },
    );
  }
}
