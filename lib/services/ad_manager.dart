import 'dart:async';
import 'dart:io' show Platform;
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

  /// Notifier to manage banner visibility.
  /// When an interstitial is showing, we set this to `false` to completely tear down the banner platform view.
  /// After the interstitial closes, we set it back to `true` to build a completely clean platform view.
  static final ValueNotifier<bool> isBannerVisibleNotifier = ValueNotifier<bool>(true);

  /// Helper counter to force a unique key on every recreation.
  static int _bannerRebuildCount = 0;

  /// Initialize the Appodeal Ads SDK. Call once in `main()`.
  /// Returns immediately, starting initialization in the background.
  static Future<void> init() async {
    _initializeAsync();
  }

  static Future<void> _initializeAsync() async {
    try {
      debugPrint('Appodeal: Initializing SDK...');
      
      // Step 1: Set testing mode (Test ads)
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
        _triggerBannerRecovery();
        loadInterstitial(); // Reload in background
      },
      onInterstitialClicked: () {
        debugPrint('Appodeal Interstitial clicked');
      },
      onInterstitialClosed: () {
        debugPrint('Appodeal Interstitial closed by user');
        _completeDismiss(true);
        _triggerBannerRecovery();
        loadInterstitial(); // Reload in background
      },
      onInterstitialExpired: () {
        debugPrint('Appodeal Interstitial expired');
        loadInterstitial(); // Reload in background
      },
    );
  }

  /// Restores the banner after a small delay to ensure native Activity transitions complete.
  static void _triggerBannerRecovery() {
    // Small delay (e.g. 200ms) to let the Android full-screen interstitial Activity completely exit
    // and restore the main Flutter Activity focus.
    Future.delayed(const Duration(milliseconds: 200), () {
      _bannerRebuildCount++;
      isBannerVisibleNotifier.value = true;
      debugPrint('Appodeal: Re-enabled banner visibility with key index: $_bannerRebuildCount');
    });
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

    // Hide and dispose the banner platform view immediately before displaying interstitial
    isBannerVisibleNotifier.value = false;
    debugPrint('Appodeal: Hid banner in preparation for interstitial overlay.');

    _dismissCompleter = Completer<bool>();

    try {
      await Appodeal.show(AppodealAdType.Interstitial);
      return await _dismissCompleter!.future;
    } catch (e) {
      debugPrint('Appodeal show error: $e');
      _completeDismiss(false);
      _triggerBannerRecovery();
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
/// Listens to [AdManager.isBannerVisibleNotifier] and checks if its own enclosing route is active via [ModalRoute.isCurrent].
///
/// Under Appodeal's single-active-banner constraint, having multiple screens containing a banner (Home and Editor)
/// concurrently in the navigation stack causes background screens to lose native ad binding.
///
/// By checking [ModalRoute.isCurrent], the background screens automatically collapse their banner view into [SizedBox.shrink()],
/// disposing of the native platform view. When returning to the screen (e.g. popping Editor to return to Home),
/// the route's status changes back to current, automatically triggering a rebuild to construct a brand new native platform view
/// with a unique key based on the route's hashCode and global count, seamlessly grabbing the active banner binding.
class AdBannerWidget extends StatefulWidget {
  const AdBannerWidget({super.key});

  @override
  State<AdBannerWidget> createState() => _AdBannerWidgetState();
}

class _AdBannerWidgetState extends State<AdBannerWidget> {
  bool _isRouteCurrent = false;
  bool _shouldRenderAd = false;
  Timer? _delayTimer;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final isCurrent = ModalRoute.of(context)?.isCurrent ?? true;
    if (isCurrent != _isRouteCurrent) {
      _isRouteCurrent = isCurrent;
      _delayTimer?.cancel();
      if (_isRouteCurrent) {
        _shouldRenderAd = false;
        // Introduce a small delay (500ms) to ensure any previous screen's banner
        // has been fully disposed before we start building the new one.
        _delayTimer = Timer(const Duration(milliseconds: 500), () {
          if (mounted) {
            setState(() {
              _shouldRenderAd = true;
            });
          }
        });
      } else {
        _shouldRenderAd = false;
      }
    }
  }

  @override
  void dispose() {
    _delayTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: AdManager.isBannerVisibleNotifier,
      builder: (context, isVisible, child) {
        // If the route is inactive or we are waiting for the cooldown delay,
        // or the banner is explicitly hidden (e.g., during interstitial)
        if (!_isRouteCurrent || !_shouldRenderAd || !isVisible) {
          if (!_isRouteCurrent) {
            return const SizedBox.shrink();
          }
          // Preserve space of 50dp to prevent layout shifting during transition
          return const SizedBox(height: 50);
        }
        
        final routeHash = ModalRoute.of(context)?.hashCode ?? 0;

        return Container(
          alignment: Alignment.center,
          color: Colors.transparent,
          height: 50,
          child: AppodealBanner(
            key: ValueKey('appodeal_banner_${routeHash}_${AdManager._bannerRebuildCount}'),
            adSize: AppodealBannerSize.BANNER,
            placement: 'default',
          ),
        );
      },
    );
  }
}
