Source: https://docs.appodeal.com/ios/data-protection/app-tracking-transparency/

Version: 

On this page

# App Tracking Transparency

Starting in iOS 14.5, IDFA will be unavailable until an app calls the
[App Tracking Transparency](https://developer.apple.com/documentation/apptrackingtransparency)
framework to present the app-tracking
authorization request to the end-user. If an app does not present this
request, the IDFA will automatically be zeroed out, which may lead to a
significant loss in ad revenue.

To display the App Tracking Transparency authorization request for
accessing the IDFA, update your `Info.plist` to add the
`NSUserTrackingUsageDescription` key with a custom message describing
the usage.

```
<key>NSUserTrackingUsageDescription</key>  
<string>This identifier will be used to deliver personalized ads to you.</string>
```

And **AppTrackingTransparency.framework** to your project.

![](/assets/ideal-img/113870096.93af309.3360.png)

## Stack Consent Manager[​](#stack-consent-manager "Direct link to Stack Consent Manager")

Appodeal SDK provides a simple way to integrate App Tracking Transparency.
It will obtain request status and show ATT request if needed using Stack Consent Manager framework.
You need to enable corresponding message in your AdMob account. See [this guide](/advanced/google-cmp-and-tcfv2-support) for more details.

Consent Manager integration remains the
same as in the [GDPR/CCPA section](/ios/data-protection/gdpr-and-ccpa).

Consent Manager will show ATT request only for users under **iOS 14.5**
or higher, you may want to add some notes in App Review Information
section of the app version page in App Store Connect. For example, it
can be something like: **App Tracking Transparency request is only
available for users under iOS 14.5 or higher.** This step may be needed
because Apple can reject builds that contain
AppTrackingTransparency.framework, but do not display ATT requests at
app launch.

## Manually[​](#manually "Direct link to Manually")

Call `requestTrackingAuthorizationWithCompletionHandler:` to present the
App Tracking Transparency authorization request alert. Call this method
at the application launch event. We recommend initializing Appodeal SDK
in the completion block.

- Swift
- Objective-C

```
import AppTrackingTransparency  
import AdSupport  
  
class AppDelegate : UIApplicationDelegate {  
  
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplicationLaunchOptionsKey: Any]?) -> Bool {  
        ATTrackingManager.requestTrackingAuthorization() { status in  
            // Tracking authorization completed. Initialise Appodeal here.  
        }  
        return true  
    }  
}
```

```
#import <AppTrackingTransparency/AppTrackingTransparency.h>  
#import <AdSupport/AdSupport.h>  
  
@implementation AppDelegate  
  
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {  
    [ATTrackingManager requestTrackingAuthorizationWithCompletionHandler:^(ATTrackingManagerAuthorizationStatus status) {  
        // Tracking authorization completed. Initialise Appodeal here.  
    }];  
    return YES;  
}
```

---