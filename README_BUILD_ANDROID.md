# BERRY Lite — Android Build Guide

## 🚀 One-Click Setup (Recommended)

For a **completely fresh Windows 10 machine**, use the master setup script:

```bash
python setup_and_build.py
```

This single command will:
1. Check your Windows version
2. **Automatically download & install** Flutter SDK
3. **Automatically download & install** Java JDK 17
4. **Automatically download & install** Android SDK + build tools
5. Configure all environment variables (PATH, ANDROID_HOME, JAVA_HOME)
6. Run `flutter doctor` to verify
7. Run `build_android.py` to compile the APK
8. Launch the app on a connected device/emulator

On **subsequent runs**, it detects existing installations and shows an interactive menu:

```
  [1] Rebuild APK + Install & Run
  [2] Hot Reload (development session)
  [3] Rebuild APK only (no install)
  [4] Run flutter doctor (diagnostics)
  [5] Fresh re-install everything
  [q] Quit
```

---

## Build Script (`build_android.py`)

The `build_android.py` script handles day-to-day build & development:

```bash
python build_android.py                  # Full check + build debug APK
python build_android.py --analyze        # Only static analysis
python build_android.py --release        # Build release APK
python build_android.py --hot-reload     # Launch flutter run with Hot Reload
python build_android.py --install        # Build + auto-install on device
python build_android.py --install --device <id>  # Target specific device
```

### New: **Hot Reload** (`--hot-reload`)

Launches a `flutter run` session with full Hot Reload support:

| Key | Action |
|-----|--------|
| `r` | Hot reload (inject code changes instantly) |
| `R` | Hot restart (full restart, preserves state) |
| `h` | Show all available commands |
| `q` | Quit |
| `d` | Detach (leave app running, exit terminal) |

Hot Reload requires a connected device or running emulator.

---

## Build Phases

| Phase | Description |
|-------|-------------|
| **Phase 0** | Project Check — verifies lib/main.dart exists |
| **Phase 1** | Environment Check — Flutter, Android SDK, Java, devices |
| **Phase 2** | Resolve Dependencies — `flutter pub get` |
| **Phase 3** | Static Analysis — `flutter analyze` |
| **Phase 4** | Build APK **or** Hot Reload session |
| **Phase 5** | Install & Launch on device (optional) |

---

## Logging

Build and setup logs are stored in `build_logs/` (**separate** from app runtime error logs in `error_logs/`):

| Log Type | Location |
|----------|----------|
| Build logs | `build_logs/build_android_YYYYMMDD_HHMMSS.log` |
| Setup logs | `build_logs/setup_YYYYMMDD_HHMMSS.log` |
| State cache | `build_logs/.setup_state.json` / `build_logs/.build_state.json` |
| App runtime logs | `<app_documents>/error_logs/berry_errors.log` |

---

## Prerequisites (Manual Setup)

If you prefer to set up manually instead of using `setup_and_build.py`:

### 1. Flutter SDK
- Download: https://docs.flutter.dev/get-started/install/windows
- Verify: `flutter doctor`

### 2. Android Studio (with Android SDK)
- Download: https://developer.android.com/studio
- Install: SDK Platform (API 34+), Build-Tools, Platform-Tools, Emulator

### 3. Java JDK 17+
- Download: https://adoptium.net/
- Verify: `java -version`

### 4. Python 3.9+
- Verify: `python --version`

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
| `flutter: command not found` | Run `setup_and_build.py` for auto-install, or add Flutter `bin/` to PATH |
| `Android SDK not found` | Set `ANDROID_HOME` env var or run `setup_and_build.py` |
| `Java not found` | Install JDK 17+ and set `JAVA_HOME`, or run `setup_and_build.py` |
| `BUILD FAILED` | Run `flutter doctor -v` for detailed diagnostics |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Uninstall existing app from device first |
| `No connected devices` | Start an emulator or connect a phone with USB debugging |

---

## Output

- **APK location**: `build/app/outputs/flutter-apk/app-debug.apk`
- **Build log**: `build_logs/build_android_YYYYMMDD_HHMMSS.log`
- **Setup log**: `build_logs/setup_YYYYMMDD_HHMMSS.log`
