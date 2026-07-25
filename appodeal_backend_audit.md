# Appodeal GDPR & CCPA Data Protection Compliance Audit Report

**Date of Audit:** July 25, 2026  
**Auditor:** Antigravity AI  
**Target Applications:**  
- **Android App:** `com.richylite.richyLite` (Appodeal Key: `1e61cf1304d32d47bbbe6c7f6f230eb445645aca570c8414`)
- **iOS App:** `com.richylite.richyLite` (Appodeal Key: `987791e06065c466883864bcd7adda11098f31b7c7a9a290`)

---

## 📋 Executive Summary

This audit evaluates the compliance of the **RICHY Lite** mobile application (Android & iOS versions) with global data protection standards—specifically the **General Data Protection Regulation (GDPR)** in the European Economic Area (EEA) and the **California Consumer Privacy Act (CCPA)** in the United States—in accordance with the official [Appodeal GDPR and CCPA Documentation](https://docs.appodeal.com/unity/data-protection/gdpr-and-ccpa).

The audit involved a comprehensive review of:
1. **Appodeal Backend Configurations** queried in real-time via the Appodeal Applications Management API.
2. **Local Source Code** and platform-specific configurations (`ad_manager.dart`, `home_screen.dart`, `AndroidManifest.xml`, `Info.plist`).
3. **Privacy Policy Disclosures** (`docs/index.html` and in-app Dialog).
4. **App-Ads.txt Verification** crawled in real-time at the developer's root domain.

> [!IMPORTANT]
> **Audit Update (July 25, 2026): 🎉 CRITICAL RISK RESOLVED**  
> The developer has successfully uploaded a comprehensive `app-ads.txt` file to the root domain (`https://richardchung0907.github.io/app-ads.txt`). This resolves the single largest risk of **zero ad delivery/zero revenue** across all major mediated networks (AppLovin, IronSource, Unity Ads). Crawlers can now verify the authorized publisher status.

> [!WARNING]
> **Remaining Action Items: ⚠️ PARTIALLY COMPLIANT**  
> While the monetization pipeline and automatic consent flow upon SDK initialization (v4.2.0) are fully functional, the app still lacks **GDPR consent revocation triggers** and a **CCPA opt-out button (Privacy Options Entry Point)** in the local Flutter UI. The hosted privacy policy also requires minor text updates.

---

## 📡 Appodeal Backend Settings (API Audit)

The following configurations were successfully queried from the Appodeal backend using the Applications API (`https://api-services.appodeal.com/api/v2/apps`):

### 🤖 Android Application Configuration
```json
{
  "app_key": "1e61cf1304d32d47bbbe6c7f6f230eb445645aca570c8414",
  "platform_name": "google",
  "platform_id": 1,
  "name": "RICHY Lite",
  "package_name": "com.richylite.richyLite",
  "orientation": "both",
  "is_for_kids": false,
  "coppa": false,
  "deleted": false
}
```

### 🍏 iOS Application Configuration
```json
{
  "app_key": "987791e06065c466883864bcd7adda11098f31b7c7a9a290",
  "platform_name": "iTunes",
  "platform_id": 4,
  "name": "RICHY - Korean Style Filter",
  "package_name": "com.richylite.richyLite",
  "orientation": "both",
  "is_for_kids": false,
  "coppa": false,
  "deleted": false
}
```

### 🔍 Backend Config Analysis:
*   **COPPA Compliance:** Both apps are correctly configured as `"is_for_kids": false` and `"coppa": false`. Since RICHY Lite is a beauty/lifestyle photo filter app targeted at general audiences (teens and adults), this is accurate. No child-directed compliance issues are present at the backend level.
*   **Integration Check:** Both package names match exactly (`com.richylite.richyLite`), preventing SDK-to-backend handshaking mismatches.

---

## ⚖️ Detailed Compliance Matrix & Gap Analysis

| Regulation / Policy | Requirement | Current Status | Audit Details & Findings | Risk Level |
| :--- | :--- | :---: | :--- | :--- |
| **Monetization (IAB)** | **Authorized Seller Verification:** App-Ads.txt must be hosted on the root domain of the developer website. | ✅ **PASS** | The developer has successfully hosted the file at `https://richardchung0907.github.io/app-ads.txt`. Live retrieval confirmed the presence of `appodeal.com, 265764, DIRECT` along with hundreds of authorized reseller lines. This authorizes all major demand partners to serve ads. | **🟢 OK** |
| **GDPR (Art. 7.3)** | **Consent Revocation (Withdrawal):** Users must be able to withdraw consent as easily as they gave it. | ❌ **FAIL** | There is **no option** anywhere in the app UI (e.g., in Settings or the Info Dialog) that allows a user to trigger `Appodeal.ConsentForm.revoke()` or re-display the consent settings form. Once consent is given, it is permanent unless the user clears the app storage. | **🔴 HIGH** |
| **CCPA / US State Laws** | **Privacy Options / Opt-Out Entry Point:** An "opt-out" mechanism must be provided on-demand for US/California users. | ❌ **FAIL** | Since US regulations operate on an opt-out model, Appodeal's Stack Consent Manager **does not automatically show** a dialog at startup. Instead, publishers are required to provide a visible "Privacy Settings" or "Do Not Sell" button in the app that triggers Appodeal's privacy option form. The codebase currently lacks any implementation for checking privacy options status or displaying this form. | **🔴 HIGH** |
| **Appodeal Policy** | **Data Collection Disclosures:** The privacy policy must explicitly disclose what data is collected by the SDK. | ⚠️ **PARTIAL** | The policy at [docs/index.html](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/docs/index.html) lists only "Device Identifiers (Google Advertising ID, iOS IDFA)". It is missing explicit disclosures for other data collected by Appodeal (IP addresses, location, device specifications, screen size, battery, timezone) and ad-event tracking (impressions, clicks). | **🟡 MEDIUM** |
| **Appodeal Policy** | **Third-Party Policy Links:** Direct links to Appodeal's Privacy Policy must be provided. | ⚠️ **PARTIAL** | While `docs/index.html` correctly links to Appodeal's policy, the **in-app Privacy Dialog** shown in `HomeScreen` only has a brief summary and a link to the GitHub Pages site. It does not provide direct legal links or disclose third-party mediation networks. | **🟡 MEDIUM** |
| **iOS Platform** | **App Tracking Transparency (ATT):** iOS 14.5+ requires explicit tracking permission. | ✅ **PASS** | `Info.plist` correctly declares `NSUserTrackingUsageDescription` with a clear explanation of IDFA usage. Additionally, the latest Appodeal SDK 4.x automates the prompt trigger. | **🟢 OK** |
| **Android Platform** | **Google Play Advertising ID:** Android 12+ requires declaring the `AD_ID` permission. | ✅ **PASS** | `AndroidManifest.xml` correctly declares `<uses-permission android:name="com.google.android.gms.permission.AD_ID" />`. | **🟢 OK** |

---

## 🛠️ Codebase Technical Audit Details

### 1. Appodeal SDK Initialization (`lib/services/ad_manager.dart`)
```dart
      await Appodeal.initialize(
        appKey: key,
        adTypes: [
          AppodealAdType.Interstitial,
          AppodealAdType.Banner,
        ],
        onInitializationFinished: (errors) { ... }
      );
```
*   **Audit Observation:** The initialization is standard and triggers the automatic consent dialog for the EU region under Appodeal 3.0+. However, initializing Appodeal unconditionally in `main()` without verifying if a user requires pre-consent screen loading can lead to minor layout jumps if the native consent dialog takes a moment to render.

### 2. Lack of CCPA & GDPR Re-consent API Integrations
In the entire codebase, there are zero calls to the following essential Appodeal Consent Manager methods:
*   `Appodeal.ConsentForm.loadAndShowIfRequired` (or manual `load` and `show` sequences)
*   `Appodeal.ConsentForm.revoke()` (critical for GDPR compliance)
*   Checking of US privacy opt-out eligibility or options.

### 3. In-App Privacy Information Dialog (`lib/screens/home_screen.dart`)
```dart
                  child: IconButton(
                    icon: const Icon(Icons.info_outline, color: Colors.grey),
                    onPressed: () {
                      showDialog(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Privacy Policy'),
                          content: Column(
                            ...
                            children: [
                              const Text('RICHY Lite values your privacy. We use device identifiers solely to deliver relevant advertisements.'),
                              ...
```
*   **Audit Observation:** This dialog is too brief to meet strict GDPR requirements. It doesn't link to the third-party providers (Appodeal, AppLovin, IronSource, etc.) and offers no interactive settings to toggle consent or opt-out.

---

## 🎯 Gaps & Actionable Recommendations (For Future Implementation)

While your immediate goal is solely to audit and not to write fixes, the following recommendations should be considered during the next development phase to achieve complete global compliance and maximize your iOS/Android ad revenue.

### 1. Implement a "Privacy Settings" Dialog / Consent Revocation
To comply with GDPR Art. 7.3, add a button labeled **"Privacy Settings"** or **"Manage Consent"** inside the app (e.g., in a dedicated settings screen or inside the info dialog).
*   **Action:** When clicked, it should check if the user is in a regulated region or use `Appodeal.ConsentForm.revoke()` to clear previous decisions and reload the standard Appodeal Consent / Privacy Options Form.

### 2. Implement CCPA "Do Not Sell My Info" for US/California Users
*   **Action:** Programmatically check if CCPA options are relevant for the user and display a **"Do Not Sell or Share My Personal Information"** link or button. Tapping this button should trigger Appodeal's opt-out settings dialog.

### 3. Comprehensive Privacy Policy Disclosures Update
The hosted Privacy Policy at `docs/index.html` must be updated to fully list all categories of personal data Appodeal handles:
> **Required Policy Update Copy:**
> *"We utilize Appodeal as a third-party ad mediation provider. Appodeal and its ad network partners may collect and process device-specific information (such as IP address, device model, operating system, screen size, battery status, timezone), location data (for regional targeting), and ad interaction logs (impressions, clicks, completed views). For more information, please see [Appodeal's Privacy Policy](https://appodeal.com/privacy-policy/)."*

### 4. AdMob Placeholder in App-Ads.txt Cleanup
*   **Action:** In `https://richardchung0907.github.io/app-ads.txt` line 25, the entry is `google.com, Publisher_ID, DIRECT, f08c47fec0942fa0`. Since your Google AdMob account was disabled, this placeholder does not affect other Appodeal networks, but it generates crawler warnings inside Google's search logs. It is recommended to **delete or comment out the Google AdMob line** in your hosted `app-ads.txt` to maintain a completely clean file.

---

### ⚠️ Legal Disclaimer
*This audit report represents a technical analysis of the app's software implementation and backend settings against Appodeal's development guidelines. It does not constitute formal legal advice. Compliance with regional laws like GDPR, CCPA, and COPPA should be reviewed and validated by qualified legal counsel prior to global store deployment.*
