Source: https://docs.appodeal.com/ios/data-protection/privacy-manifest/

Version: 

On this page

# Privacy Manifest

At WWDC23 Apple introduced privacy manifests to describe the data your app or third-party SDK collects and the reasons required APIs it uses. You can find additional
information on [Apple Developer website](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files)

Privacy updates for App Store submissions

Starting May 1, 2024, Apple will reject apps submitted to the App Store if those apps contain an SDK that uses a
Required Reasons API without declaring that API in its privacy manifest.

If you have integrated Appodeal SDK via Cocoapods, you can always get access to `PrivacyInfo.xcprivacy` file by
path `Pods/Appodeal/Appodeal-3.3.2/Appodeal.xcframework/ios-arm64/Appodeal.framework/PrivacyInfo.xcprivacy`

## Required Reason APIs[​](#required-reason-apis "Direct link to Required Reason APIs")

To clarify the usage of Required Reason APIs, app developers will be required to declare the API category and specify the reasons for using the API.
Below are the Appodeal APIs and their usage.
You can copy the following code which includes the Required Reasons above, and paste it within your PrivacyInfo.xcprivacy file.

info

At the moment due to lack of information we cannot recommend you whether to add or not these Accesses API Types to your own
Privacy Manifest. After getting any changes we will update the documentation.

```
<key>NSPrivacyAccessedAPITypes</key>  
	<array>  
		<dict>  
			<key>NSPrivacyAccessedAPIType</key>  
			<string>NSPrivacyAccessedAPICategoryUserDefaults</string>  
			<key>NSPrivacyAccessedAPITypeReasons</key>  
			<array>  
				<string>CA92.1</string>  
			</array>  
		</dict>  
		<dict>  
			<key>NSPrivacyAccessedAPIType</key>  
			<string>NSPrivacyAccessedAPICategoryFileTimestamp</string>  
			<key>NSPrivacyAccessedAPITypeReasons</key>  
			<array>  
				<string>C617.1</string>  
			</array>  
		</dict>  
	</array>
```

## Compliance[​](#compliance "Direct link to Compliance")

Adapters and SDK versions implemented in Appodeal 3.3.2 and whether or not they comply with Apple’s privacy manifest requirements.

| Ad Network | SDK Version | Is compliant | Notes |
| --- | --- | --- | --- |
| Adjust | 4.38.0 | Yes |  |
| Amazon | 4.9.0 | Yes |  |
| Applovin | 12.4.1 | Yes |  |
| AppsFlyer | 6.13.1 | **No** | AppsFlyer has alreay added their Privacy Manifest but the latest version cannot be implemented because of the abcence of proper Unity Plugin |
| BidMachine | 2.6.0 | Yes |  |
| Bidon | 0.4.8 | Yes |  |
| Bigo | 4.2.2 | Yes |  |
| Criteo | 6.0.0 | Yes |  |
| DTExchange | 8.2.7 | Yes | DTExchange Nutrition labels are not being displayed in generated Privacy Report |
| **Facebook** | 16.0.1 | **No** | Facebook has alreay added their Privacy Manifest but the latest version cannot be implemented because of the abcence of proper Unity Plugin |
| Firebase | 10.22.0 | Yes |  |
| Google Ad Mob | 10.14.0 | **No** | Google Ad Mob has alreay added their Privacy Manifest in their latest version, which will be implemented in the future release |
| InMobi | 10.7.1 | Yes |  |
| IronSource | 10.7.1 | Yes |  |
| Meta Audience | 6.15.0 | Yes |  |
| Mintegral | 7.6.1 | Yes | Mintegral Nutrition labels are not being displayed in generated Privacy Report |
| **MyTarget** | 5.20.1 | **No** | MyTarget SDK has not added Privacy Manifest yet |
| Pangle | 5.8.0 | Yes |  |
| Sentry | 8.23.0 | Yes |  |
| Smaato | 22.8.2 | Yes |  |
| **Tapjoy** | 12.11.0 | **No** | Tapjoy has alreay added their Privacy Manifest in their latest version, which will be implemented in the future release |
| Unity | 4.10.0 | Yes |  |
| Vungle | 7.3.0 | Yes |  |
| **Yandex** | 5.2.1 | **No** | Yandex updates are temporary stopped |

info

At the moment due to lack of information we cannot recommend you what to do with ad networks and their adapters which do not have
Privacy Manifest in Appodeal SDK 3.3.2. After getting any changes we will update the documentation.