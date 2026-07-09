# BERRY Lite — iOS Build Guide

## ⚠️ Important: iOS builds require macOS

Building iOS apps natively **requires a Mac with Xcode**. If you're on Windows or Linux, use one of the cloud build options below.

---

## Option A: Cloud Build via EAS (Recommended for non-Mac users)

Expo Application Services (EAS) provides cloud-based iOS builds without owning a Mac.

### Setup

```bash
# 1. Install EAS CLI
npm install -g eas-cli

# 2. Login to Expo (free account)
eas login

# 3. Run the build script (creates eas.json + guides you)
python build_ios.py --eas

# 4. Trigger iOS build
eas build --platform ios --profile preview
```

### Requirements
- Node.js + npm (for EAS CLI)
- Expo account (free tier: 30 builds/month)
- Apple Developer account ($99/year) for distribution/TestFlight builds

---

## Option B: Local Build (macOS only)

### Prerequisites

1. **macOS** (Ventura 13+ recommended)
2. **Xcode 15+** from the App Store
3. **CocoaPods**: `sudo gem install cocoapods`
4. **Flutter SDK**: https://docs.flutter.dev/get-started/install/macos

### Build

```bash
# Full environment check
python build_ios.py --checkonly

# Local build (debug, for simulator)
python build_ios.py --local
```

---

## Option C: Alternative Cloud Services

| Service | Description |
|---------|-------------|
| **Codemagic** | CI/CD with free macOS minutes, easy Flutter integration |
| **GitHub Actions** | macOS runners available, great for CI pipeline |
| **MacStadium** | Rent a dedicated Mac in the cloud |
| **MacinCloud** | Pay-as-you-go Mac cloud access |

---

## The Build Script

The iOS build script (`build_ios.py`) does the following:

| Phase | Description |
|-------|-------------|
| **Phase 1** | Platform check, Flutter SDK, Xcode, CocoaPods, Expo tools |
| **Phase 2** | `flutter pub get` |
| **Phase 3** | Build decision — local or cloud guidance |

### Commands

```bash
python build_ios.py              # Environment check + guidance
python build_ios.py --checkonly  # Only check environment
python build_ios.py --eas        # EAS cloud build setup
python build_ios.py --local      # Local build (macOS only)
```

---

## iOS Permissions

The following permissions are pre-configured in `ios/Runner/Info.plist`:

- **NSCameraUsageDescription** — Camera access for taking photos
- **NSPhotoLibraryUsageDescription** — Photo library access for picking images
- **NSPhotoLibraryAddUsageDescription** — Permission to save edited photos

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `xcodebuild: command not found` | Install Xcode from App Store, then `sudo xcode-select --switch /Applications/Xcode.app` |
| `CocoaPods not found` | `sudo gem install cocoapods` |
| `No such module` errors | `cd ios && pod install && cd ..` |
| `Provisioning profile` errors | Configure signing in Xcode or use `--no-codesign` for simulator |
| `eas: command not found` | `npm install -g eas-cli` |
