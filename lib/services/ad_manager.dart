import 'dart:async';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:app_tracking_transparency/app_tracking_transparency.dart';

/// Manages Google AdMob Interstitial ads for RICHY Lite.
///
/// Uses Google's official **test ad IDs** during development
/// to prevent account suspension.
class AdManager {
  AdManager._();

  // TODO: REPLACE WITH PRODUCTION UNIT ID
  static const String _fallbackAndroidUnitId = 'ca-app-pub-3940256099942544/1033173712';
  // TODO: REPLACE WITH PRODUCTION UNIT ID
  static const String _fallbackIOSUnitId = 'ca-app-pub-3940256099942544/4411468910';

  static const String _productionAndroidUnitId = String.fromEnvironment('ADMOB_ANDROID_UNIT_ID');
  static const String _productionIOSUnitId = String.fromEnvironment('ADMOB_IOS_UNIT_ID');

  static String get _adUnitId {
    if (kDebugMode) {
      return Platform.isAndroid ? _fallbackAndroidUnitId : _fallbackIOSUnitId;
    }
    final prodId = Platform.isAndroid ? _productionAndroidUnitId : _productionIOSUnitId;
    return prodId.isNotEmpty ? prodId : (Platform.isAndroid ? _fallbackAndroidUnitId : _fallbackIOSUnitId);
  }

  static InterstitialAd? _interstitial;
  static bool _isLoading = false;
  static Completer<bool>? _dismissCompleter;
  
  static final Completer<void> _consentCompleter = Completer<void>();
  static DateTime? _lastAdShownTime;

  /// Initialize the Mobile Ads SDK. Call once in `main()`.
  /// Returns immediately, starting initialization in the background.
  static Future<void> init() async {
    _initializeAsync();
  }

  static Future<void> _initializeAsync() async {
    try {
      // Step 1: UMP Consent Flow with 5-second timeout
      await _requestConsent().timeout(
        const Duration(seconds: 5),
        onTimeout: () {
          debugPrint('UMP Consent request timed out.');
        },
      );

      // Step 2: Request ATT on iOS
      if (Platform.isIOS) {
        final status = await AppTrackingTransparency.trackingAuthorizationStatus;
        if (status == TrackingStatus.notDetermined) {
          await AppTrackingTransparency.requestTrackingAuthorization();
        }
      }

      // Set COPPA & GDPR-K Configurations
      final requestConfiguration = RequestConfiguration(
        tagForChildDirectedTreatment: TagForChildDirectedTreatment.yes,
        tagForUnderAgeOfConsent: TagForUnderAgeOfConsent.yes,
      );
      await MobileAds.instance.updateRequestConfiguration(requestConfiguration);

      // Step 3: Initialize Google Mobile Ads SDK
      await MobileAds.instance.initialize();
    } catch (e) {
      debugPrint('AdManager init error: $e');
    } finally {
      if (!_consentCompleter.isCompleted) {
        _consentCompleter.complete();
      }
    }
  }

  static Future<void> _requestConsent() async {
    final completer = Completer<void>();

    final params = ConsentRequestParameters();
    
    ConsentInformation.instance.requestConsentInfoUpdate(
      params,
      () async {
        if (await ConsentInformation.instance.isConsentFormAvailable()) {
          ConsentForm.loadAndShowConsentFormIfRequired((loadAndShowError) {
            if (loadAndShowError != null) {
              debugPrint('Consent form load/show error: ${loadAndShowError.message}');
            }
            if (!completer.isCompleted) completer.complete();
          });
        } else {
          if (!completer.isCompleted) completer.complete();
        }
      },
      (FormError error) {
        debugPrint('Consent info update error: ${error.message}');
        if (!completer.isCompleted) completer.complete();
      },
    );

    return completer.future;
  }

  /// Preload an interstitial ad.
  static Future<void> loadInterstitial() async {
    await _consentCompleter.future;

    if (_isLoading || _interstitial != null) return;

    _isLoading = true;
    await InterstitialAd.load(
      adUnitId: _adUnitId,
      request: const AdRequest(),
      adLoadCallback: InterstitialAdLoadCallback(
        onAdLoaded: (InterstitialAd ad) {
          _interstitial = ad;
          _isLoading = false;

          ad.fullScreenContentCallback = FullScreenContentCallback(
            onAdDismissedFullScreenContent: (_) {
              _disposeAd();
              _completeDismiss(true);
              loadInterstitial(); // Background reload
            },
            onAdFailedToShowFullScreenContent: (_, AdError error) {
              _disposeAd();
              _completeDismiss(false);
              loadInterstitial(); // Background reload
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
  /// Returns `false` if no ad was available, failed to show, or frequency cap not met.
  static Future<bool> showInterstitial() async {
    await _consentCompleter.future;

    // Frequency capping: 3-minute minimum delay
    if (_lastAdShownTime != null) {
      final diff = DateTime.now().difference(_lastAdShownTime!);
      if (diff.inMinutes < 3) {
        return false;
      }
    }

    if (_interstitial == null) {
      loadInterstitial();
      return false;
    }

    _lastAdShownTime = DateTime.now();
    _dismissCompleter = Completer<bool>();

    try {
      await _interstitial!.show();
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
