#!/usr/bin/env python3
"""
BERRY Lite — Android Build & Test Script
=========================================
This script automates the Android build pipeline for BERRY Lite:
  1. Checks local environment (Flutter, Android SDK, Java)
  2. Detects connected devices / running emulators
  3. Runs `flutter pub get` and `flutter analyze`
  4. Builds a debug APK for local testing
  5. Optionally installs & launches on connected device

Usage:
    python build_android.py            # Full check + build
    python build_android.py --analyze  # Only static analysis
    python build_android.py --release  # Build release APK
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PROJECT_DIR, "error_logs", f"build_android_{datetime.now():%Y%m%d_%H%M%S}.log")


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
    path = shutil.which(name)
    if path:
        return path
    # Windows fallback: check common Flutter install paths
    if platform.system() == "Windows":
        candidates = [
            os.path.expandvars(r"%USERPROFILE%\flutter\bin\flutter.bat"),
            os.path.expandvars(r"%LOCALAPPDATA%\flutter\bin\flutter.bat"),
            r"C:\flutter\bin\flutter.bat",
            r"C:\src\flutter\bin\flutter.bat",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
    return None


# ── Check Functions ───────────────────────────────────────────────

def check_flutter() -> bool:
    """Check Flutter SDK availability and version."""
    log("── Checking Flutter SDK ──")
    flutter = find_executable("flutter")
    if not flutter:
        log("  ✗ Flutter not found on PATH!")
        log("    Install Flutter: https://docs.flutter.dev/get-started/install")
        log("    Or set FLUTTER_ROOT environment variable.")
        return False

    result = run([flutter, "--version"], timeout=60)
    if result.returncode != 0:
        log(f"  ✗ Flutter command failed:\n{result.stderr}")
        return False

    # Extract version line
    for line in result.stdout.splitlines():
        if "Flutter" in line and ("channel" in line or "•" in line):
            log(f"  ✓ {line.strip()}")
            break
    return True


def check_android_sdk() -> bool:
    """Check Android SDK and required tools."""
    log("── Checking Android SDK ──")

    # Check ANDROID_HOME / ANDROID_SDK_ROOT
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not android_home:
        # Flutter default
        if platform.system() == "Windows":
            default = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk")
        else:
            default = os.path.expanduser("~/Android/Sdk")
        if os.path.isdir(default):
            android_home = default
            os.environ["ANDROID_HOME"] = android_home
        else:
            log("  ✗ Android SDK not found!")
            log("    Install Android Studio: https://developer.android.com/studio")
            return False

    log(f"  ✓ ANDROID_HOME = {android_home}")

    # Check platform-tools (adb)
    adb = os.path.join(android_home, "platform-tools", "adb")
    if platform.system() == "Windows":
        adb += ".exe"
    if os.path.isfile(adb):
        log(f"  ✓ ADB found: {adb}")
    else:
        log("  ⚠ ADB not found in platform-tools")

    # Check build-tools
    build_tools_dir = os.path.join(android_home, "build-tools")
    if os.path.isdir(build_tools_dir):
        versions = os.listdir(build_tools_dir)
        if versions:
            log(f"  ✓ Build-tools versions: {', '.join(versions)}")
    else:
        log("  ⚠ No build-tools found")

    return True


def check_java() -> bool:
    """Check Java JDK availability."""
    log("── Checking Java JDK ──")
    java = find_executable("java")
    if not java:
        # Check JAVA_HOME
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java = os.path.join(java_home, "bin", "java")
            if platform.system() == "Windows":
                java += ".exe"
    if java and os.path.isfile(java):
        result = run([java, "-version"], timeout=30)
        version_line = result.stderr.splitlines()[0] if result.stderr else "unknown"
        log(f"  ✓ Java: {version_line}")
        return True
    else:
        log("  ⚠ Java not found on PATH. Required for Android builds.")
        log("    Install JDK 17+: https://adoptium.net/")
        return False


def check_devices() -> list[str]:
    """Check for connected Android devices / emulators."""
    log("── Checking Android Devices ──")
    flutter = find_executable("flutter")
    if not flutter:
        return []

    adb = None
    android_home = os.environ.get("ANDROID_HOME", "")
    if android_home:
        adb_path = os.path.join(android_home, "platform-tools", "adb")
        if platform.system() == "Windows":
            adb_path += ".exe"
        if os.path.isfile(adb_path):
            adb = adb_path

    if not adb:
        adb = find_executable("adb")

    if adb:
        result = run([adb, "devices"], timeout=30)
        devices = []
        for line in result.stdout.splitlines()[1:]:
            if line.strip() and "\tdevice" in line:
                device_id = line.split("\t")[0]
                devices.append(device_id)
                log(f"  ✓ Device connected: {device_id}")
        if not devices:
            log("  ℹ No devices/emulators detected. You can still build APK.")
        return devices
    else:
        log("  ℹ ADB not found — skipping device check.")
        return []


# ── Build Functions ───────────────────────────────────────────────

def flutter_pub_get() -> bool:
    """Run flutter pub get."""
    log("── Running flutter pub get ──")
    flutter = find_executable("flutter")
    result = run([flutter, "pub", "get"], timeout=120)
    if result.returncode == 0:
        log("  ✓ Dependencies resolved")
        return True
    else:
        log(f"  ✗ Failed:\n{result.stderr}")
        return False


def flutter_analyze() -> bool:
    """Run flutter analyze for static analysis."""
    log("── Running flutter analyze ──")
    flutter = find_executable("flutter")
    result = run([flutter, "analyze"], timeout=180)
    if result.returncode == 0:
        log("  ✓ No analysis issues found")
        return True
    else:
        log(f"  ⚠ Analysis found issues:\n{result.stdout[-2000:]}")
        # Don't fail the build for warnings in test phase
        return True


def build_apk(release: bool = False) -> str | None:
    """Build APK (debug or release)."""
    mode = "release" if release else "debug"
    log(f"── Building {mode} APK ──")

    flutter = find_executable("flutter")
    cmd = [flutter, "build", "apk"]
    if release:
        cmd.append("--release")
    else:
        cmd.append("--debug")

    result = run(cmd, timeout=600)
    if result.returncode == 0:
        # Find the APK
        build_dir = os.path.join(
            PROJECT_DIR, "build", "app", "outputs", "flutter-apk"
        )
        apk_name = f"app-{mode}.apk"
        apk_path = os.path.join(build_dir, apk_name)
        if os.path.isfile(apk_path):
            size_mb = os.path.getsize(apk_path) / (1024 * 1024)
            log(f"  ✓ APK built: {apk_path}")
            log(f"    Size: {size_mb:.1f} MB")
            return apk_path
        else:
            log(f"  ⚠ APK not found at expected path: {apk_path}")
            # Try to find it
            for root, dirs, files in os.walk(build_dir):
                for f in files:
                    if f.endswith(".apk"):
                        found = os.path.join(root, f)
                        log(f"  ✓ Found APK: {found}")
                        return found
            return None
    else:
        log(f"  ✗ Build failed:\n{result.stderr[-2000:]}")
        return None


def install_and_launch(apk_path: str, device_id: str | None = None) -> bool:
    """Install APK on device and launch the app."""
    log("── Installing on device ──")

    flutter = find_executable("flutter")
    cmd = [flutter, "install"]
    if device_id:
        cmd.extend(["-d", device_id])

    result = run(cmd, timeout=120)
    if result.returncode == 0:
        log("  ✓ App installed and launched")
        return True
    else:
        log(f"  ✗ Install failed:\n{result.stderr}")
        return False


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BERRY Lite — Android Build & Test Script"
    )
    parser.add_argument(
        "--analyze", action="store_true", help="Only run static analysis"
    )
    parser.add_argument(
        "--release", action="store_true", help="Build release APK instead of debug"
    )
    parser.add_argument(
        "--install", action="store_true", help="Install and launch on connected device"
    )
    args = parser.parse_args()

    log("=" * 60)
    log("  BERRY Lite — Android Build Script")
    log(f"  Platform: {platform.system()} {platform.release()}")
    log(f"  Project:  {PROJECT_DIR}")
    log("=" * 60)

    # ── Phase 1: Environment Check ─────────────────────────────
    log("\n▶ Phase 1: Environment Check")

    flutter_ok = check_flutter()
    if not flutter_ok:
        log("\n✗ Cannot proceed without Flutter SDK. Exiting.")
        sys.exit(1)

    android_ok = check_android_sdk()
    java_ok = check_java()

    if not android_ok:
        log("\n⚠ Android SDK issues detected. Build may fail.")
    if not java_ok:
        log("\n⚠ Java not found. Build may fail.")

    devices = check_devices()

    # ── Phase 2: Resolve Dependencies ──────────────────────────
    log("\n▶ Phase 2: Resolve Dependencies")
    if not flutter_pub_get():
        log("\n✗ Failed to resolve dependencies. Exiting.")
        sys.exit(1)

    # ── Phase 3: Static Analysis ───────────────────────────────
    log("\n▶ Phase 3: Static Analysis")
    flutter_analyze()

    if args.analyze:
        log("\n✓ Analysis complete. Exiting (--analyze mode).")
        return

    # ── Phase 4: Build APK ─────────────────────────────────────
    log("\n▶ Phase 4: Build APK")
    apk_path = build_apk(release=args.release)
    if not apk_path:
        log("\n✗ APK build failed.")
        sys.exit(1)

    # ── Phase 5: Install & Launch (optional) ───────────────────
    log("\n▶ Phase 5: Install & Test")
    if args.install and devices:
        install_and_launch(apk_path, devices[0])
    elif args.install and not devices:
        log("  ⚠ No devices found. APK is ready at:")
        log(f"    {apk_path}")
        log("  Transfer to device and install manually, or start an emulator.")
    else:
        log(f"  ℹ APK ready at: {apk_path}")
        if devices:
            log("  Run with --install to auto-install on connected device.")

    log("\n" + "=" * 60)
    log("  ✓ Build complete!")
    log(f"  Log file: {LOG_FILE}")
    log("=" * 60)


if __name__ == "__main__":
    main()
