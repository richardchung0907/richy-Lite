Source: https://docs.appodeal.com/ios/data-protection/coppa/

Version: 

# COPPA

For purposes of the [Children's Online Privacy Protection Act (COPPA)](https://business.ftc.gov/privacy-and-security/children%27s-privacy)
there is a setting called childDirectedTreatment. If your app is
designed for kids you can disable sending user data to ad networks by
calling the method below.

Should be called before the SDK initialization.

- Swift
- Objective-C

```
Appodeal.setChildDirectedTreatment(true)
```

```
[Appodeal setChildDirectedTreatment: YES]
```

info

Call `setChildDirectedTreatment()` method with `true` to indicate that you want your content treated as child-directed
for purposes of COPPA.

Call `setChildDirectedTreatment()` method with `false` to indicate that you don't want your content treated as
child-directed for purposes of COPPA.

---