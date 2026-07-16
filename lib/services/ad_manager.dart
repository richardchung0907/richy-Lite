import 'dart:async';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
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

  // Banner Test IDs
  static const String _fallbackAndroidBannerUnitId = 'ca-app-pub-3940256099942544/6300978111';
  static const String _fallbackIOSBannerUnitId = 'ca-app-pub-3940256099942544/2934735716';

  static const String _productionAndroidBannerUnitId = String.fromEnvironment('ADMOB_ANDROID_BANNER_UNIT_ID');
  static const String _productionIOSBannerUnitId = String.fromEnvironment('ADMOB_IOS_BANNER_UNIT_ID');

  static String get _adUnitId {
    if (kDebugMode) {
      return Platform.isAndroid ? _fallbackAndroidUnitId : _fallbackIOSUnitId;
    }
    final prodId = Platform.isAndroid ? _productionAndroidUnitId : _productionIOSUnitId;
    return prodId.isNotEmpty ? prodId : (Platform.isAndroid ? _fallbackAndroidUnitId : _fallbackIOSUnitId);
  }

  static String get _bannerAdUnitId {
    if (kDebugMode) {
      return Platform.isAndroid ? _fallbackAndroidBannerUnitId : _fallbackIOSBannerUnitId;
    }
    final prodId = Platform.isAndroid ? _productionAndroidBannerUnitId : _productionIOSBannerUnitId;
    return prodId.isNotEmpty ? prodId : (Platform.isAndroid ? _fallbackAndroidBannerUnitId : _fallbackIOSBannerUnitId);
  }

  static InterstitialAd? _interstitial;
  static bool _isLoading = false;
  static Completer<bool>? _dismissCompleter;
  
  static final Completer<void> _consentCompleter = Completer<void>();

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

      // Remove COPPA & GDPR-K Configurations that force all users to be treated as children
      final requestConfiguration = RequestConfiguration(
        tagForChildDirectedTreatment: TagForChildDirectedTreatment.unspecified,
        tagForUnderAgeOfConsent: TagForUnderAgeOfConsent.unspecified,
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

    if (_interstitial == null) {
      loadInterstitial();
      return false;
    }

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

/// A wrapper widget that loads and displays a BannerAd.
class AdBannerWidget extends StatefulWidget {
  const AdBannerWidget({Key? key}) : super(key: key);

  @override
  State<AdBannerWidget> createState() => _AdBannerWidgetState();
}

class _AdBannerWidgetState extends State<AdBannerWidget> {
  BannerAd? _bannerAd;
  bool _isLoaded = false;
  Orientation? _currentOrientation;
  double? _currentWidth;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final orientation = MediaQuery.of(context).orientation;
    final width = MediaQuery.of(context).size.width;

    // Reload the ad if the orientation or width changes significantly.
    if (_currentOrientation != orientation || _currentWidth != width) {
      _currentOrientation = orientation;
      _currentWidth = width;
      _loadAd();
    }
  }

  Future<void> _loadAd() async {
    // Ensure we have consent before loading banner ads
    await AdManager._consentCompleter.future;

    if (!mounted) return;

    final width = MediaQuery.of(context).size.width.truncate();
    final size = await AdSize.getCurrentOrientationAnchoredAdaptiveBannerAdSize(width);

    if (size == null || !mounted) {
      return;
    }

    final oldBanner = _bannerAd;

    _bannerAd = BannerAd(
      adUnitId: AdManager._bannerAdUnitId,
      size: size,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (Ad ad) {
          debugPrint('BannerAd loaded.');
          if (mounted) {
            setState(() {
              _isLoaded = true;
            });
          } else {
            ad.dispose();
          }
        },
        onAdFailedToLoad: (Ad ad, LoadAdError error) {
          debugPrint('BannerAd failed to load: $error');
          ad.dispose();
          _bannerAd = null;
        },
      ),
    );

    await _bannerAd!.load();
    oldBanner?.dispose();
  }

  @override
  void dispose() {
    _bannerAd?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_bannerAd != null && _isLoaded) {
      return Container(
        color: Colors.transparent,
        width: _bannerAd!.size.width.toDouble(),
        height: _bannerAd!.size.height.toDouble(),
        child: AdWidget(ad: _bannerAd!),
      );
    }
    return const SizedBox.shrink();
  }
}
