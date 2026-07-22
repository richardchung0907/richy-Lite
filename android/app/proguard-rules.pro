# Appodeal & Bidon ProGuard Rules
# Prevent R8 compilation failures due to missing optional third-party classes within Appodeal and its Bidon mediation adapters

-dontwarn org.bidon.**
-keep class org.bidon.** { *; }

-dontwarn com.appodeal.**
-keep class com.appodeal.** { *; }

# Also preserve generic Android view structures for PlatformViews
-keep class android.view.** { *; }
