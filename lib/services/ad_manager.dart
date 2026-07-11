import 'dart:async';

import 'package:google_mobile_ads/google_mobile_ads.dart';

/// Manages Google AdMob Interstitial ads for RICHY Lite.
///
/// Uses Google's official **test ad IDs** during development
/// to prevent account suspension.
///
/// Key: `showInterstitial()` uses a `Completer` so callers can
/// `await` until the user actually dismisses (or the ad fails),
/// preventing the share sheet from opening on top of the ad.
class AdManager {
  AdManager._();

  // ── Test Ad IDs (Google official) ───────────────────────────
  static const String _androidTestAdUnitId =
      'ca-app-pub-3940256099942544/1033173712';
  static const String _iOSTestAdUnitId =
      'ca-app-pub-3940256099942544/4411468910';

  static InterstitialAd? _interstitial;
  static bool _isLoading = false;
  static Completer<bool>? _dismissCompleter;

  /// Initialize the Mobile Ads SDK. Call once in `main()`.
  static Future<void> init() async {
    await MobileAds.instance.initialize();
  }

  /// Preload an interstitial ad.
  static Future<void> loadInterstitial() async {
    if (_isLoading || _interstitial != null) return;

    _isLoading = true;
    await InterstitialAd.load(
      adUnitId: _androidTestAdUnitId,
      request: const AdRequest(),
      adLoadCallback: InterstitialAdLoadCallback(
        onAdLoaded: (InterstitialAd ad) {
          _interstitial = ad;
          _isLoading = false;

          ad.fullScreenContentCallback = FullScreenContentCallback(
            onAdDismissedFullScreenContent: (_) {
              _disposeAd();
              // Signal the completer that user dismissed the ad
              _completeDismiss(true);
              loadInterstitial();
            },
            onAdFailedToShowFullScreenContent: (_, AdError error) {
              _disposeAd();
              // Ad failed to show — release the await anyway
              _completeDismiss(false);
              loadInterstitial();
            },
          );
        },
        onAdFailedToLoad: (LoadAdError error) {
          _interstitial = null;
          _isLoading = false;
          Future.delayed(const Duration(seconds: 10), loadInterstitial);
        },
      ),
    );
  }

  /// Show the interstitial ad and **wait until the user dismisses it**.
  ///
  /// Returns `true` if the ad was shown AND user dismissed it normally.
  /// Returns `false` if no ad was available or the ad failed to show.
  static Future<bool> showInterstitial() async {
    if (_interstitial == null) {
      loadInterstitial();
      return false;
    }

    // Create a fresh Completer for this show cycle
    _dismissCompleter = Completer<bool>();

    try {
      await _interstitial!.show();
      // Wait for user to dismiss the ad (or ad to fail)
      return await _dismissCompleter!.future;
    } catch (_) {
      _disposeAd();
      _completeDismiss(false);
      loadInterstitial();
      return false;
    }
  }

  static void _disposeAd() {
    _interstitial?.dispose();
    _interstitial = null;
  }

  static void _completeDismiss(bool value) {
    if (_dismissCompleter != null && !_dismissCompleter!.isCompleted) {
      _dismissCompleter!.complete(value);
    }
    _dismissCompleter = null;
  }

  /// Dispose resources. Call when app is shutting down.
  static void dispose() {
    _disposeAd();
    _dismissCompleter = null;
    _isLoading = false;
  }
}
