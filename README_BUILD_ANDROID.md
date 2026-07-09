# BERRY Lite — Android Build Guide

## Prerequisites

Before running the Android build script, ensure the following are installed:

### 1. Flutter SDK
- Download: https://docs.flutter.dev/get-started/install/windows
- Verify: `flutter doctor`
- The build script auto-detects Flutter from PATH or common install locations.

### 2. Android Studio (with Android SDK)
- Download: https://developer.android.com/studio
- In Android Studio → SDK Manager, install:
  - Android SDK Platform (API 34+)
  - Android SDK Build-Tools
  - Android SDK Platform-Tools (includes ADB)
  - Android Emulator (optional but recommended)

### 3. Java JDK 17+
- Download: https://adoptium.net/
- Verify: `java -version`

### 4. Python 3.9+
- Already installed on most systems.
- Verify: `python --version`

---

## Quick Start

```bash
# Full build (check environment → resolve deps → build debug APK)
python build_android.py

# Only check environment & static analysis (no build)
python build_android.py --analyze

# Build release APK (signed, for distribution)
python build_android.py --release

# Build + auto-install on connected device/emulator
python build_android.py --install
```

---

## Build Phases

The script runs through these phases:

| Phase | Description |
|-------|-------------|
| **Phase 1** | Environment Check — Flutter, Android SDK, Java, connected devices |
| **Phase 2** | Resolve Dependencies — `flutter pub get` |
| **Phase 3** | Static Analysis — `flutter analyze` |
| **Phase 4** | Build APK — `flutter build apk --debug` (or `--release`) |
| **Phase 5** | Install & Test — optional: installs APK on connected device |

---

## Setting Up an Android Emulator

1. Open Android Studio → Device Manager
2. Create a new virtual device (Pixel 7, API 34 recommended)
3. Launch the emulator
4. Run: `python build_android.py --install`

---

## Connecting a Physical Device

1. Enable **Developer Options** on your Android phone:
   - Settings → About Phone → Tap "Build Number" 7 times
2. Enable **USB Debugging** in Developer Options
3. Connect via USB and accept the RSA key prompt
4. Verify: `adb devices` (should show your device)
5. Run: `python build_android.py --install`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `flutter: command not found` | Add Flutter `bin/` to your PATH environment variable |
| `Android SDK not found` | Set `ANDROID_HOME` env var to your SDK path (e.g., `%LOCALAPPDATA%\Android\Sdk`) |
| `Java not found` | Install JDK 17+ and set `JAVA_HOME` |
| `BUILD FAILED` | Run `flutter doctor -v` for detailed diagnostics |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Uninstall existing app from device first |

---

## Output

- **APK location**: `build/app/outputs/flutter-apk/app-debug.apk`
- **Build log**: `error_logs/build_android_YYYYMMDD_HHMMSS.log`
