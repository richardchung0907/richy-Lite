# Appodeal & Bidon ProGuard Rules
# Prevent R8 compilation failures due to missing optional third-party classes within Appodeal and its Bidon mediation adapters

-dontwarn org.bidon.**
-keep class org.bidon.** { *; }

-dontwarn com.appodeal.**
-keep class com.appodeal.** { *; }

# Also preserve generic Android view structures for PlatformViews
-keep class android.view.** { *; }

# WorkManager R8/ProGuard rules to prevent initialization crashes
-keep class androidx.work.impl.background.systemalarm.SystemAlarmService { *; }
-keep class androidx.work.impl.background.systemjob.SystemJobService { *; }
-keep class androidx.work.impl.foreground.SystemForegroundService { *; }
-keep class * extends androidx.work.impl.scheduler.Scheduler { *; }
-keep class * extends androidx.work.impl.WorkDatabase { *; }
-keep class androidx.work.impl.WorkDatabase_Impl { *; }

# Room & SQLite database rules (used by WorkManager internally)
-keep class * extends androidx.room.RoomDatabase { *; }
-dontwarn androidx.room.multiinstance.**
-dontwarn androidx.sqlite.db.framework.**
