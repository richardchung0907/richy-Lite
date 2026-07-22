#!/usr/bin/env python3
"""
RICHY Lite — iOS Build & Test Script
=====================================
This script handles iOS build for RICHY Lite. Since iOS builds
require macOS with Xcode, this script:
  1. Checks the local platform (warns if not macOS)
  2. Scans for available build tools:
     - Flutter SDK
     - Xcode / Xcode CLI tools
     - CocoaPods
     - Expo tools (expo-cli, eas-cli) — for alternative cloud builds
  3. If on macOS: builds via `flutter build ios`
  4. If not on macOS: guides user to use EAS (Expo Application Services)
     for cloud-based iOS builds
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime

# ── Paths & Setup ──────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

LOG_FILE = os.path.join(PROJECT_DIR, "error_logs", f"build_ios_{datetime.now():%Y%m%d_%H%M%S}.log")
IS_MACOS = platform.system() == "Darwin"


def log(msg: str):
    """Print and append to log file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a command and return its result."""
    log(f"  RUN: {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd or PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=(platform.system() == "Windows"),
    )


def find_executable(name: str) -> str | None:
    """Find an executable on PATH."""
    return shutil.which(name)


# ── Check Functions ───────────────────────────────────────────────

def check_platform() -> bool:
    """Check if we're on macOS."""
    log("── Checking Platform ──")
    if IS_MACOS:
        log(f"  ✓ Running on macOS {platform.mac_ver()[0]}")
        return True
    else:
        log(f"  ⚠ Running on {platform.system()} {platform.release()}")
        log("    iOS builds require macOS with Xcode.")
        log("    Will guide you through cloud build options instead.")
        return False


def check_flutter() -> bool:
    """Check Flutter SDK availability."""
    log("── Checking Flutter SDK ──")
    flutter = find_executable("flutter")
    if not flutter:
        log("  ✗ Flutter not found on PATH!")
        return False

    result = run([flutter, "--version"], timeout=60)
    if result.returncode != 0:
        log(f"  ✗ Flutter command failed")
        return False

    for line in result.stdout.splitlines():
        if "Flutter" in line and ("channel" in line or "•" in line):
            log(f"  ✓ {line.strip()}")
            break
    return True


def check_xcode() -> bool:
    """Check Xcode availability (macOS only)."""
    log("── Checking Xcode ──")
    if not IS_MACOS:
        log("  ⤐ Skipped (not macOS)")
        return False

    # Check xcodebuild
    xcodebuild = find_executable("xcodebuild")
    if xcodebuild:
        result = run([xcodebuild, "-version"], timeout=30)
        if result.returncode == 0:
            version_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
            log(f"  ✓ Xcode: {version_line}")
        else:
            log("  ⚠ xcodebuild found but returned error")
    else:
        log("  ✗ Xcode not found. Install from App Store.")
        log("    https://apps.apple.com/app/xcode/id497799835")
        return False

    # Check Xcode CLI tools
    result = run(["xcode-select", "-p"], timeout=30)
    if result.returncode == 0:
        log(f"  ✓ CLI tools: {result.stdout.strip()}")
    else:
        log("  ⚠ Xcode CLI tools not configured.")
        log("    Run: xcode-select --install")

    return True


def check_cocoapods() -> bool:
    """Check CocoaPods availability."""
    log("── Checking CocoaPods ──")
    pod = find_executable("pod")
    if pod:
        result = run([pod, "--version"], timeout=30)
        if result.returncode == 0:
            log(f"  ✓ CocoaPods: {result.stdout.strip()}")
            return True

    log("  ⚠ CocoaPods not found.")
    if IS_MACOS:
        log("    Install: sudo gem install cocoapods")
    else:
        log("    CocoaPods is only needed for local macOS builds.")
    return False


def check_expo_tools() -> dict[str, bool]:
    """Check for Expo ecosystem tools."""
    log("── Checking Expo Tools ──")

    tools = {}

    # Expo CLI
    expo = find_executable("expo")
    if expo:
        result = run(["npx", "expo", "--version"], timeout=30)
        if result.returncode == 0:
            log(f"  ✓ Expo CLI: {result.stdout.strip()}")
            tools["expo_cli"] = True
        else:
            log("  ⚠ Expo CLI found but returned error")
            tools["expo_cli"] = False
    else:
        log("  ℹ Expo CLI not found (install: npm install -g expo-cli)")
        tools["expo_cli"] = False

    # EAS CLI (most important for cloud builds)
    eas = find_executable("eas")
    if eas:
        result = run(["eas", "--version"], timeout=30)
        if result.returncode == 0:
            log(f"  ✓ EAS CLI: {result.stdout.strip()}")
            tools["eas_cli"] = True
        else:
            log("  ⚠ EAS CLI found but returned error")
            tools["eas_cli"] = False
    else:
        log("  ℹ EAS CLI not found")
        log("    Install: npm install -g eas-cli")
        tools["eas_cli"] = False

    # Check if npx can run eas
    result = run(["npx", "eas-cli", "--version"], timeout=30)
    if result.returncode == 0:
        log("  ✓ EAS CLI available via npx")
        tools["eas_npx"] = True
    else:
        tools["eas_npx"] = False

    # Expo Go (check via npm)
    result = run(["npx", "expo", "whoami"], timeout=30)
    if result.returncode == 0:
        log(f"  ✓ Expo account logged in: {result.stdout.strip()}")
        tools["expo_login"] = True
    else:
        log("  ℹ Not logged into Expo account")
        tools["expo_login"] = False

    # Check node/npm (required for Expo tools)
    node = find_executable("node")
    npm = find_executable("npm")
    if node and npm:
        node_ver = run(["node", "--version"], timeout=30)
        npm_ver = run(["npm", "--version"], timeout=30)
        log(f"  ✓ Node: {node_ver.stdout.strip()}, npm: {npm_ver.stdout.strip()}")
        tools["node_ok"] = True
    else:
        log("  ✗ Node.js/npm required for Expo tools")
        tools["node_ok"] = False

    return tools


def check_flutter_ios_config() -> bool:
    """Check that Flutter iOS project is configured."""
    log("── Checking Flutter iOS Config ──")
    ios_dir = os.path.join(PROJECT_DIR, "ios")
    if not os.path.isdir(ios_dir):
        log("  ✗ ios/ directory not found!")
        log("    Run `flutter create --platforms=ios .` to generate.")
        return False

    # Check Podfile
    podfile = os.path.join(ios_dir, "Podfile")
    if os.path.isfile(podfile):
        log("  ✓ Podfile exists")
    else:
        log("  ⚠ Podfile missing — will be generated on build")

    return True


# ── Build Functions ───────────────────────────────────────────────

def flutter_pub_get() -> bool:
    """Run flutter pub get."""
    log("── Running flutter pub get ──")
    flutter = find_executable("flutter")
    if not flutter:
        return False
    result = run([flutter, "pub", "get"], timeout=120)
    if result.returncode == 0:
        log("  ✓ Dependencies resolved")
        return True
    else:
        log(f"  ✗ Failed:\n{result.stderr[-1000:]}")
        return False


def build_ios_local() -> bool:
    """Build iOS app locally (macOS only with Xcode)."""
    if not IS_MACOS:
        log("  ✗ Local iOS builds require macOS.")
        return False

    log("── Building iOS (debug, no codesign) ──")

    flutter = find_executable("flutter")
    if not flutter:
        return False

    # Build without codesigning for simulator testing
    result = run(
        [flutter, "build", "ios", "--debug", "--no-codesign"],
        timeout=600,
    )
    if result.returncode == 0:
        log("  ✓ iOS build successful!")
        log("    Run `flutter run` or open ios/Runner.xcworkspace in Xcode.")
        return True
    else:
        log(f"  ✗ iOS build failed:\n{result.stderr[-2000:]}")
        return False


def setup_eas_build() -> bool:
    """Guide the user through EAS cloud build setup."""
    log("── EAS Cloud Build Setup ──")
    log("")
    log("  EAS (Expo Application Services) lets you build iOS apps")
    log("  in the cloud without a Mac. Here's how:")
    log("")
    log("  1. Install EAS CLI:")
    log("     npm install -g eas-cli")
    log("")
    log("  2. Login to your Expo account:")
    log("     eas login")
    log("")
    log("  3. Configure the project for EAS:")
    log("     eas build:configure")
    log("     (This creates eas.json in the project root)")
    log("")
    log("  4. Trigger an iOS build:")
    log("     eas build --platform ios --profile preview")
    log("")
    log("  5. For ad-hoc/TestFlight distribution:")
    log("     eas build --platform ios --profile production")
    log("")
    log("  Note: EAS cloud builds require an Expo account (free tier")
    log("  includes 30 builds/month). An Apple Developer account")
    log("  ($99/year) is required for distribution builds.")
    log("")
    log("  ── Alternative: Use a cloud Mac service ──")
    log("  Services like MacStadium, MacinCloud, or GitHub Actions")
    log("  with macOS runners can also build iOS apps.")
    log("")
    return True


def create_eas_json() -> bool:
    """Create a basic eas.json if it doesn't exist."""
    eas_json_path = os.path.join(PROJECT_DIR, "eas.json")
    if os.path.isfile(eas_json_path):
        log("  ℹ eas.json already exists")
        return True

    log("── Creating eas.json ──")
    import json

    config = {
        "cli": {"version": ">= 10.0.0"},
        "build": {
            "preview": {
                "ios": {
                    "simulator": False,
                    "distribution": "internal",
                }
            },
            "production": {
                "ios": {
                    "distribution": "store",
                    "autoIncrement": True,
                }
            },
        },
        "submit": {
            "production": {
                "ios": {
                    "appleId": "YOUR_APPLE_ID@example.com",
                    "ascAppId": "YOUR_APP_STORE_CONNECT_APP_ID",
                    "appleTeamId": "YOUR_TEAM_ID",
                }
            }
        },
    }

    with open(eas_json_path, "w") as f:
        json.dump(config, f, indent=2)
    log("  ✓ Created eas.json (edit with your credentials)")
    return True


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="RICHY Lite — iOS Build & Test Script"
    )
    parser.add_argument(
        "--eas", action="store_true",
        help="Setup and guide EAS cloud build"
    )
    parser.add_argument(
        "--checkonly", action="store_true",
        help="Only check environment, don't build"
    )
    parser.add_argument(
        "--local", action="store_true",
        help="Attempt local iOS build (macOS only)"
    )
    args = parser.parse_args()

    log("=" * 60)
    log("  RICHY Lite — iOS Build Script")
    log(f"  Platform: {platform.system()} {platform.release()}")
    log(f"  Project:  {PROJECT_DIR}")
    log("=" * 60)

    # ── Phase 1: Platform & Environment Check ──────────────────
    log("\n▶ Phase 1: Environment Check")

    is_macos = check_platform()
    flutter_ok = check_flutter()

    if not flutter_ok:
        log("\n✗ Flutter SDK required. Exiting.")
        sys.exit(1)

    if is_macos:
        check_xcode()
        check_cocoapods()

    check_flutter_ios_config()
    expo_tools = check_expo_tools()

    if args.checkonly:
        log("\n" + "=" * 60)
        log("  ✓ Environment check complete!")
        log(f"  Log file: {LOG_FILE}")
        log("=" * 60)
        return

    # ── Phase 2: Resolve Dependencies ──────────────────────────
    log("\n▶ Phase 2: Resolve Dependencies")
    if not flutter_pub_get():
        log("\n✗ Failed to resolve dependencies.")
        sys.exit(1)

    # ── Phase 3: Build Decision ────────────────────────────────
    log("\n▶ Phase 3: Build")

    if args.eas:
        # EAS cloud build path
        create_eas_json()
        setup_eas_build()
    elif args.local and is_macos:
        # Local iOS build
        build_ios_local()
    elif is_macos:
        log("  ℹ On macOS — use --local for local build or --eas for cloud.")
        log("    Local build:  python build_ios.py --local")
        log("    Cloud build:  python build_ios.py --eas")
    else:
        # Not on macOS — guide to cloud build
        log("  ⚠ iOS builds require macOS.")
        log("")
        log("  ── Recommended: Use EAS Cloud Build ──")
        log("    Run: python build_ios.py --eas")
        log("")
        log("  ── Alternatives ──")
        log("  1. Use a cloud Mac (MacStadium, MacinCloud)")
        log("  2. GitHub Actions with macOS runner")
        log("  3. Codemagic CI/CD (macOS builds in cloud)")
        log("  4. Borrow a friend's MacBook for 10 minutes ☕")

    log("\n" + "=" * 60)
    log("  ✓ iOS build script complete!")
    log(f"  Log file: {LOG_FILE}")
    log("=" * 60)


if __name__ == "__main__":
    main()
