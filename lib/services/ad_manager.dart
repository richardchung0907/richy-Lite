import 'package:google_mobile_ads/google_mobile_ads.dart';

/// Manages Google AdMob Interstitial ads for RICHY Lite.
///
/// Uses Google's official **test ad IDs** during development
/// to prevent account suspension.
///
/// Lifecycle:
///   1. Call `AdManager.init()` once at app startup
///   2. Call `AdManager.loadInterstitial()` to preload an ad
///   3. Call `AdManager.showInterstitial()` to display it
///      (automatically reloads after dismissal/failure)
///
/// On dismiss/failure, the next ad loads immediately so it's
/// ready for the following session.
class AdManager {
  AdManager._();

  // ── Test Ad IDs (Google official) ───────────────────────────
  static const String _androidTestAdUnitId =
      'ca-app-pub-3940256099942544/1033173712';
  static const String _iOSTestAdUnitId =
      'ca-app-pub-3940256099942544/4411468910';

  static InterstitialAd? _interstitial;
  static bool _isLoading = false;
  static bool _isShowing = false;

  /// Initialize the Mobile Ads SDK. Call once in `main()`.
  static Future<void> init() async {
    await MobileAds.instance.initialize();
  }

  /// Preload an interstitial ad. Safe to call repeatedly;
  /// skips if already loading or an ad is ready.
  static Future<void> loadInterstitial() async {
    if (_isLoading || _isShowing) return;

    _isLoading = true;
    await InterstitialAd.load(
      adUnitId: _androidTestAdUnitId, // ← Replace with real ID in production
      request: const AdRequest(),
      adLoadCallback: InterstitialAdLoadCallback(
        onAdLoaded: (InterstitialAd ad) {
          _interstitial = ad;
          _isLoading = false;

          ad.fullScreenContentCallback = FullScreenContentCallback(
            onAdShowedFullScreenContent: (_) {
              _isShowing = true;
            },
            onAdDismissedFullScreenContent: (_) {
              _interstitial?.dispose();
              _interstitial = null;
              _isShowing = false;
              // Auto-reload for next use
              loadInterstitial();
            },
            onAdFailedToShowFullScreenContent: (_, AdError error) {
              _interstitial?.dispose();
              _interstitial = null;
              _isShowing = false;
              // Reload on failure
              loadInterstitial();
            },
          );
        },
        onAdFailedToLoad: (LoadAdError error) {
          _interstitial = null;
          _isLoading = false;
          // Retry after a brief delay to avoid spam
          Future.delayed(const Duration(seconds: 10), loadInterstitial);
        },
      ),
    );
  }

  /// Show the interstitial ad if one is loaded.
  ///
  /// Returns `true` if ad was shown, `false` if no ad was available.
  /// Callers should NOT block critical user flows on this result.
  static Future<bool> showInterstitial() async {
    if (_interstitial == null) {
      // No ad ready — load one for next time
      loadInterstitial();
      return false;
    }

    try {
      await _interstitial!.show();
      return true;
    } catch (_) {
      _interstitial?.dispose();
      _interstitial = null;
      _isShowing = false;
      loadInterstitial();
      return false;
    }
  }

  /// Dispose the current ad. Call when the app is shutting down.
  static void dispose() {
    _interstitial?.dispose();
    _interstitial = null;
    _isLoading = false;
    _isShowing = false;
  }
}
