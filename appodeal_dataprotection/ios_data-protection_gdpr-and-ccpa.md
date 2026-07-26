Source: https://docs.appodeal.com/ios/data-protection/gdpr-and-ccpa/

Version: 

On this page

# GDPR and CCPA

info

Keep in mind that it’s best to contact qualified legal professionals, if you haven’t done so already, to get more
information and be well-prepared for compliance.

[The General Data Protection Regulation](https://gdpr-info.eu/), better known as GDPR, took effect on May 25, 2018.
It's a set of rules designed to give EU citizens more control over their personal data.
Any *businesses established in the EU or with users based in Europe are required to comply with GDPR or risk facing heavy fines*.
The California Consumer Privacy Act (CCPA) went into effect on January 1, 2020.
**We have put together some guidelines to help publishers understand better the steps they need to take to be GDPR compliant.**

You can learn more about GDPR and CCPA and their differences [here](https://iapp.org/resources/article/ccpa-and-gdpr-comparison-chart/).

---

## Step 1. Update Privacy Policy[​](#step-1-update-privacy-policy "Direct link to Step 1. Update Privacy Policy")

### Include Additional Information To Your Privacy Policy[​](#include-additional-information-to-your-privacy-policy "Direct link to Include Additional Information To Your Privacy Policy")

Don’t forget to add information about IP address and advertising ID collection, as well as
[the link to Appodeal’s privacy policy](https://www.appodeal.com/privacy-policy)
to your app’s privacy policy on the App Store.

To speed up the process, you could use
[privacy policy generators](https://app-privacy-policy-generator.firebaseapp.com/) -
just insert advertising ID, IP address, and location (if you collect users’ location) in the **Personally Identifiable
Information you collect** field (in line with other information about your app) and
[the link to Appodeal’s privacy policy](https://www.appodeal.com/privacy-policy)
in the **Link to the privacy policy of third party service providers used by the app** field.

### Add A Privacy Policy To Your Mobile App[​](#add-a-privacy-policy-to-your-mobile-app "Direct link to Add A Privacy Policy To Your Mobile App")

You must add your explicit privacy policies in two places: on your app’s Store Listing page and within your app.

You can find detailed instructions on adding your privacy policy to your app on legal service websites.
For example, Iubenda, the solution tailored to legal compliance, provides
[a comprehensive guide](https://www.iubenda.com/en/help/401-privacy-policy-for-ios-and-macos-apps)
on including a privacy policy in your app.

Make sure that your privacy policy website has an SSL certificate—this point might seem obvious,
but it’s still essential.

Here are two useful resources that you can utilize while working on your app compliance:

- [Privacy, Security and Deception regulations (by Google Play)](https://play.google.com/intl/en-GB_ALL/about/privacy-security-deception/user-data)
- [Recommendations on Developing a Meaningful Privacy Policy (by Attorney General California Department of Justice)](https://oag.ca.gov/sites/all/files/agweb/pdfs/cybersecurity/making_your_privacy_practices_public.pdf)

note

Please note that although we’re always eager to back you up with valuable information, we’re not authorized
to provide any legal advice. It’s important to address your questions to lawyers who specialize in this area.

---

## Step 2. Configure Stack Consent Manager with TCF v2 Support[​](#step-2-configure-stack-consent-manager-with-tcf-v2-support "Direct link to Step 2. Configure Stack Consent Manager with TCF v2 Support")

info

Since `Appodeal SDK 3.2.1` it is fully compatible with Google UMP and supports IAB TCF v2.

In order for Appodeal and our ad providers to deliver ads that are more relevant to your users, as a mobile app publisher,
you need to collect explicit user consent in the regions covered by GDPR.

To get consent for collecting personal data of your users, we suggest you use a ready-made solution -
Stack Consent Manager based on **Google User Messaging Platform (UMP)**.

Configure Google UMP

Before you start, you need to configure Google UMP. Follow [this instruction](/advanced/google-cmp-and-tcfv2-support) to setup a consent form.

---

## Step 3. Integrate Stack Consent Manager[​](#step-3-integrate-stack-consent-manager "Direct link to Step 3. Integrate Stack Consent Manager")

Stack Consent Manager comes with a pre-made consent window that you can easily present to your users.
That means you no longer need to create your own consent window.

Starting from Appodeal SDK 3.0, Stack Consent Manager is included by default.

**Consent will be requested automatically on SDK initialization**, and consent form will be shown if it is
necessary without any additional calls.

Please keep in mind that Consent will be shown only in the **EU** region, you can use VPN for testing.

This means that Appodeal SDK integration code remains the same:

- Swift
- Objective-C

```
@UIApplicationMain   
final class MyAppDelegate: UIResponder, UIApplicationDelegate, AppodealInitializationDelegate {   
	func application(   
		_ application: UIApplication, didFinishLaunchingWithOptions  
		launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil ) -> Bool {  
		Appodeal.setAutocache(false, types: .interstitial)   
		Appodeal.setLogLevel(.verbose)   
  
		// New optional delegate for initialization completion 	  
		Appodeal.setInitializationDelegate(self)   
		/// Any other pre-initialization   
		/// app specific logic   
		Appodeal.initialize(   
			withApiKey: "APP_KEY",   
			types: .interstitial   
		)   
		return true   
	}   
	func appodealSDKDidInitialize() {   
		// Appodeal SDK did complete initialization   
	}   
}
```

```
@interface MyAppDelegate ()   
<AppodealInitializationDelegate>   
  
@end   
  
@implementation MyAppDelegate   
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {   
	[Appodeal setAutocache:NO types:AppodealAdTypeInterstitial];   
	[Appodeal setLogLevel:APDLogLevelVerbose];  
  
	// New optional delegate for initialization completion   
	[Appodeal setInitializationDelegate:self];   
  
	/// Any other pre-initialization   
	/// app specific logic   
	[Appodeal initializeWithApiKey:@"APP KEY" types:AppodealAdTypeInterstitial];  
	return YES;   
}   
  
- (void)appodealSDKDidInitialize {   
	// Appodeal SDK did complete initialization   
}   
  
@end
```

---

## Advanced[​](#advanced "Direct link to Advanced")

Starting from **Appodeal SDK 3.2.1** you do not have to update user consent manually.
Appodeal SDK support the iAB TCFv2 protocol. All consent data will be read from **NSUserDefaults** and
passed everywhere you may need. Even if you want to use an alternative solution for User Consent Management,
Appodeal SDK will read and not modify the consent data.

### Manual Consent Management[​](#manual-consent-management "Direct link to Manual Consent Management")

If you wish, you can manage and update consent manually using Stack Consent Manager calls.

info

Now **StackConsentManager** also supports **Swift Concurrency**.

Consent manager SDK can be synchronized and shown at any moment of application lifecycle.
We recommend to synchronize it at application launch. Multiple synchronization calls are allowed.
Appodeal SDK will not show consent dialog if it has been presented.
For more details follow the example:

- Swift
- Objective-C

```
import StackConsentManager  
  
/// Initialisation   
class YourAppDelegate: AppDelegate {  
	override func application(  
		_ application: UIApplication,   
		didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]?  
	) -> Bool {  
        let parameters = ConsentUpdateRequestParameters(  
            appKey: "YOUR_APP_KEY",  
            mediationSdkName: "YOUR_SDK_NAME",  
            mediationSdkVersion: "YOUR_SDK_VERSION",  
            COPPA: true  
        )  
          
        // requesting consent info update  
        ConsentManager.shared.requestConsentInfoUpdate(parameters: parameters) { error in  
            guard error == nil else { return } // error occured while receiving consent info  
  
            // loading and showing consent dialog  
            ConsentManager.shared.loadAndPresentIfNeeded(rootViewController: UIViewController()) { error in  
                if let error {  
                    // error occured  
                } else {  
                    // everything was fine, now you have user's consent  
                    // initialize SDK here  
                }  
            }  
        }  
		return true  
	}  
}
```

```
#import <StackConsentManager/StackConsentManager-Swift.h>  
  
@implementation YourAppDelegate  
  
/// Initialisation   
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {  
    APDConsentUpdateRequestParameters *parameters = [[APDConsentUpdateRequestParameters alloc] initWithAppKey:@"YOUR_APP_KEY" mediationSdkName:@"YOUR_SDK_NAME" mediationSdkVersion:@"YOUR_SDK_VERSION" COPPA:true];  
    // requesting consent info update  
    [APDConsentManager.shared requestConsentInfoUpdateWithParameters:parameters completion:^(NSError * error) {  
        if (error) {  
            // error occured while receiving consent info  
            return;  
        }  
          
        // loading and showing consent dialog  
        [APDConsentManager.shared loadAndPresentIfNeededWithRootViewController:[UIViewController new] completion:^(NSError *error) {  
            if (error) {  
                return; // error occured while receiving user consent  
            }  
              
            // everything was fine, now you have user's consent  
            // initialize SDK here  
        }];  
    }];  
    return YES;  
}  
  
@end
```

---

### Force Present Consent Dialog[​](#force-present-consent-dialog "Direct link to Force Present Consent Dialog")

If you want to have more control over Consent dialog, you can use the following code.
Here you load Consent dialog separately and can store a reference to it or do whatever you need.

- Swift
- Objective-C

```
/// Initialisation   
class YourAppDelegate: AppDelegate {  
	override func application(  
		_ application: UIApplication,   
		didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]?  
	) -> Bool {  
        let parameters = ConsentUpdateRequestParameters(  
            appKey: "YOUR_APP_KEY",  
            mediationSdkName: "YOUR_SDK_NAME",  
            mediationSdkVersion: "YOUR_SDK_VERSION",  
            COPPA: true  
        )  
          
        // requesting consent info update  
        ConsentManager.shared.requestConsentInfoUpdate(parameters: parameters) { error in  
            guard error == nil else { return } // error occured while receiving consent info  
  
            // loading consent dialog  
            ConsentManager.shared.load { dialog, error in  
                guard error == nil else { return } // error occured while loading consent dialog  
                  
                // showing consent dialog  
                dialog?.present(rootViewController: UIViewController(), completion: { error in  
                    guard error == nil else { return } // error occured while receiving user consent  
  
                    // everything was fine, now you have user's consent  
                    // initialize SDK here  
                })  
            }  
        }  
		return true  
	}  
}
```

```
/// Initialisation   
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {  
    APDConsentUpdateRequestParameters *parameters = [[APDConsentUpdateRequestParameters alloc] initWithAppKey:@"YOUR_APP_KEY" mediationSdkName:@"YOUR_SDK_NAME" mediationSdkVersion:@"YOUR_SDK_VERSION" COPPA:true];  
    // requesting consent info update  
    [APDConsentManager.shared requestConsentInfoUpdateWithParameters:parameters completion:^(NSError * error) {  
        if (error) {  
            return; // error occured while receiving consent info  
        }  
          
        // loading consent dialog  
        [APDConsentManager.shared loadWithCompletion:^(APDConsentDialog *dialog, NSError *error) {  
            if (error) {  
                return; // error occured while loading consent dialog  
            }  
              
            if (dialog) {  
                // showing consent dialog  
                [dialog presentWithRootViewController:[UIViewController new] completion:^(NSError *error) {  
                    if (error) {  
                        return; // error occured while receiving user consent  
                    }  
                      
                    // everything was fine, now you have user's consent  
                    // initialize SDK here  
                }];  
            }  
        }];  
    }];  
    return YES;  
}
```

`YOUR_APP_KEY` is required parameter (Appodeal APP Key)

info

SDK only allows calling consent window api after synchronization

---

### Check Consent Status[​](#check-consent-status "Direct link to Check Consent Status")

After synchronization completion, you can receive information about the previous user consent.
Before synchronization this parameter is `undefined`

- Swift
- Objective-C

```
// Check consent status  
let status = ConsentManager.shared.status
```

```
// Check consent status  
APDConsentStatus status = [APDConsentManager.shared status];
```

---

### Revoke User Consent[​](#revoke-user-consent "Direct link to Revoke User Consent")

If you need to revoke user consent, you can use the following code:

- Swift
- Objective-C

```
// Check consent status  
ConsentManager.shared.revoke()
```

```
// Check consent status  
[APDConsentManager.shared revoke];
```

---

### US State Regulations Support (Privacy Entry Point)[​](#us-state-regulations-support-privacy-entry-point "Direct link to US State Regulations Support (Privacy Entry Point)")

Available since `StackConsentManager 4.0.0` (Appodeal SDK 4.2.0).

US state privacy laws (CCPA, CPA, VCDPA, and others) follow an **opt-out model**: data
processing is allowed by default, but users must be given a permanent way to opt out — typically a
**"Do Not Sell or Share My Personal Information"** button (the *Privacy Entry Point*). In the US zone
the standard `loadAndPresentIfNeeded` flow does **not** show any form, because consent is not
required at launch — the opt-out form must be shown on demand, in response to a user tap.

To support this, Stack Consent Manager exposes two new APIs:

- `privacyOptionsRequirementStatus` — tells you whether you must surface a Privacy Entry Point
  button in your app UI.
- `showPrivacyOptionsForm(rootViewController:completion:)` — shows the US opt-out form (or the
  GDPR re-consent form when called in the EEA).

Both APIs become available after `requestConsentInfoUpdate` completes.

#### Check whether a Privacy Entry Point is required[​](#check-whether-a-privacy-entry-point-is-required "Direct link to Check whether a Privacy Entry Point is required")

Use `privacyOptionsRequirementStatus` to decide whether to render the opt-out button. The status
returns `.required` for users in regulated US states and in the EEA (for GDPR re-consent),
`.notRequired` elsewhere, and `.unknown` before `requestConsentInfoUpdate` has completed.

- Swift
- Objective-C

```
if ConsentManager.shared.privacyOptionsRequirementStatus == .required {  
    // Show a "Do Not Sell or Share My Personal Information" / Privacy Settings button  
}
```

```
if (APDConsentManager.shared.privacyOptionsRequirementStatus == APDPrivacyOptionsStatusRequired) {  
    // Show a "Do Not Sell or Share My Personal Information" / Privacy Settings button  
}
```

#### Show the Privacy Options form[​](#show-the-privacy-options-form "Direct link to Show the Privacy Options form")

Call `showPrivacyOptionsForm` from the action handler of your Privacy Entry Point button.
This is the **only** way to display the US opt-out form, and it must be triggered by an explicit
user interaction — not at app launch.

- Swift
- Objective-C

```
@IBAction func privacyOptionsButtonTapped() {  
    ConsentManager.shared.showPrivacyOptionsForm(rootViewController: self) { error in  
        if let error {  
            // handle error  
        } else {  
            // user finished interacting with the form  
        }  
    }  
}
```

Swift Concurrency:

```
try await ConsentManager.shared.showPrivacyOptionsForm(rootViewController: self)
```

```
- (IBAction)privacyOptionsButtonTapped:(id)sender {  
    [APDConsentManager.shared showPrivacyOptionsFormWithRootViewController:self  
                                                                completion:^(NSError *error) {  
        if (error) {  
            // handle error  
        } else {  
            // user finished interacting with the form  
        }  
    }];  
}
```

note

Once the user interacts with the US opt-out form, Stack Consent Manager writes the corresponding
`IABGPP_GppSID` and `IABGPP_HDR_GppString` keys to `NSUserDefaults`, where ad networks read them.
Before the form has been shown at least once, these keys remain empty and ad networks may treat
the user as "no consent collected".

### Non-Personalized Advertising[​](#non-personalized-advertising "Direct link to Non-Personalized Advertising")

Available since Appodeal SDK 4.3.0.

Consent is enforced automatically — no extra integration is required.

If you want to request non-personalized advertising regardless of the resolved consent, call
`Appodeal.setNonPersonalized(true)`. This disables the collection of data used for ad personalization,
and a publisher-set value takes precedence over the consent resolved from the CMP.
Call it before `Appodeal.initialize(...)`.

This is relevant in several scenarios:

- **Age-restricted users (US).** US state laws (CCPA/CPRA in California, and similar laws in Virginia,
  Colorado, Connecticut, and others) restrict selling or sharing the personal data of minors, and COPPA
  adds stricter rules for children under 13. Use this flag alongside
  [`setChildDirectedTreatment`](/ios/data-protection/coppa) when you cannot determine the exact age but targeting must be
  limited.
- **Users who declined personalized advertising** through your own consent flow, when they are not
  subject to a specific regulation covered by the other APIs.
- **General opt-out** — a catch-all to suppress targeting signals when none of the more specific privacy
  flags apply.

- Swift
- Objective-C

```
Appodeal.setNonPersonalized(true)
```

```
[Appodeal setNonPersonalized:YES];
```