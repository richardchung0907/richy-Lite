#!/usr/bin/env python3
"""
RICHY Lite — Android Build, Hot Reload & Test Script
======================================================
This script automates the Android pipeline for RICHY Lite:
  1. Checks local environment (Flutter, Android SDK, Java)
  2. Detects connected devices / running emulators
  3. Runs `flutter pub get` and `flutter analyze`
  4. Builds a debug APK **OR** launches Hot Reload session
  5. Optionally installs & launches on connected device

Usage:
    python build_android.py                  # Full check + build debug APK
    python build_android.py --analyze        # Only static analysis
    python build_android.py --release        # Build release APK
    python build_android.py --hot-reload     # Launch `flutter run` with Hot Reload
    python build_android.py --install        # Build + auto-install on device
"""

import argparse
import os
import platform
import shutil
import signal
import subprocess
import sys
import traceback
from datetime import datetime
from typing import Optional

# ── Configuration ─────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Build logs go to `build_logs/` (separate from app `error_logs/`)
BUILD_LOG_DIR = os.path.join(PROJECT_DIR, "build_logs")
BUILD_LOG_FILE = os.path.join(
    BUILD_LOG_DIR,
    f"build_android_{datetime.now():%Y%m%d_%H%M%S}.log",
)


def ensure_log_dir():
    """Ensure the build log directory exists."""
    os.makedirs(BUILD_LOG_DIR, exist_ok=True)


def log(msg: str):
    """Print to stdout and append to the build log file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    ensure_log_dir()
    try:
        with open(BUILD_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass  # Non-critical


def log_error(msg: str, exc: Optional[Exception] = None):
    """Log an error with optional exception traceback."""
    log(f"  ✗ ERROR: {msg}")
    if exc:
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        for line in "".join(tb).splitlines():
            log(f"    {line}")


def run(
    cmd: list[str],
    cwd: str | None = None,
    timeout: int = 300,
    capture: bool = True,
    allow_fail: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command and return its result.

    When `capture=True`, stdout/stderr are captured (good for check
    commands).  When `capture=False`, output streams live (good for
    Hot Reload / flutter run).
    """
    log(f"  RUN: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_DIR,
            capture_output=capture,
            text=True,
            timeout=timeout,
            shell=(platform.system() == "Windows") and capture,
        )
        if not allow_fail and result.returncode != 0:
            stderr_tail = (result.stderr or "")[-1500:]
            log(f"  ✗ Exit code {result.returncode}")
            if stderr_tail.strip():
                log(f"  stderr: {stderr_tail}")
        return result
    except subprocess.TimeoutExpired:
        log(f"  ✗ Command timed out after {timeout}s")
        raise
    except Exception as e:
        log_error(f"Command failed: {' '.join(cmd)}", e)
        raise


def run_live(
    cmd: list[str],
    cwd: str | None = None,
) -> subprocess.Popen:
    """Run a command with live output (for `flutter run` / Hot Reload).

    Returns the Popen handle so the caller can wait or send keystrokes.
    """
    log(f"  LIVE: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd,
        cwd=cwd or PROJECT_DIR,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        shell=(platform.system() == "Windows"),
    )


def find_executable(name: str) -> str | None:
    """Find an executable on PATH or common Flutter install locations."""
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


# ── State file for caching environment checks ────────────────────
STATE_FILE = os.path.join(PROJECT_DIR, "build_logs", ".build_state.json")

import json as _json


def load_state() -> dict:
    """Load persisted build state."""
    if os.path.isfile(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return _json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict):
    """Persist build state."""
    ensure_log_dir()
    state["last_updated"] = datetime.now().isoformat()
    try:
        with open(STATE_FILE, "w") as f:
            _json.dump(state, f, indent=2)
    except OSError:
        pass


# ── Check Functions ───────────────────────────────────────────────

def check_flutter() -> bool:
    """Check Flutter SDK availability and version."""
    log("── Checking Flutter SDK ──")
    flutter = find_executable("flutter")
    if not flutter:
        log("  ✗ Flutter not found on PATH!")
        log("    Install Flutter: https://docs.flutter.dev/get-started/install")
        log("    Or run setup_and_build.py for automatic installation.")
        return False

    result = run([flutter, "--version"], timeout=60)
    if result.returncode != 0:
        log_error("Flutter version check failed")
        log(f"  stderr: {result.stderr[-1000:]}")
        return False

    for line in result.stdout.splitlines():
        if "Flutter" in line and ("channel" in line or "•" in line):
            log(f"  ✓ {line.strip()}")
            break

    # Persist
    state = load_state()
    state["flutter_path"] = flutter
    save_state(state)
    return True


def check_android_sdk() -> bool:
    """Check Android SDK and required tools."""
    log("── Checking Android SDK ──")

    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not android_home:
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
            log("    Or run setup_and_build.py for guided installation.")
            return False

    log(f"  ✓ ANDROID_HOME = {android_home}")

    adb = os.path.join(android_home, "platform-tools", "adb")
    if platform.system() == "Windows":
        adb += ".exe"
    if os.path.isfile(adb):
        log(f"  ✓ ADB found")
    else:
        log("  ⚠ ADB not found — install platform-tools via SDK Manager")

    build_tools_dir = os.path.join(android_home, "build-tools")
    if os.path.isdir(build_tools_dir):
        versions = os.listdir(build_tools_dir)
        if versions:
            log(f"  ✓ Build-tools: {', '.join(versions)}")
    else:
        log("  ⚠ No build-tools found")

    state = load_state()
    state["android_home"] = android_home
    save_state(state)
    return True


def check_java() -> bool:
    """Check Java JDK availability."""
    log("── Checking Java JDK ──")
    java = find_executable("java")
    if not java:
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java = os.path.join(java_home, "bin", "java")
            if platform.system() == "Windows":
                java += ".exe"
    if java and os.path.isfile(java):
        result = run([java, "-version"], timeout=30)
        version_line = result.stderr.splitlines()[0] if result.stderr else "unknown"
        log(f"  ✓ Java: {version_line}")
        state = load_state()
        state["java_path"] = java
        save_state(state)
        return True
    else:
        log("  ⚠ Java not found. Required for Android builds.")
        log("    Install JDK 17+: https://adoptium.net/")
        return False


def check_devices() -> list[str]:
    """Check for connected Android devices / emulators."""
    log("── Checking Android Devices ──")

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
                log(f"  ✓ Device: {device_id}")
        if not devices:
            log("  ℹ No devices/emulators detected. Build will still succeed.")
            log("    Start an emulator or connect a phone for Hot Reload / install.")
        return devices
    else:
        log("  ℹ ADB not found — skipping device check.")
        return []


def check_project_structure() -> bool:
    """Verify that a Flutter project exists (lib/main.dart etc.)."""
    log("── Checking Project Structure ──")
    main_dart = os.path.join(PROJECT_DIR, "lib", "main.dart")
    pubspec = os.path.join(PROJECT_DIR, "pubspec.yaml")
    if os.path.isfile(main_dart) and os.path.isfile(pubspec):
        log("  ✓ Flutter project detected")
        return True
    log("  ✗ lib/main.dart or pubspec.yaml missing!")
    return False


# ── Build & Hot Reload Functions ──────────────────────────────────

def flutter_pub_get() -> bool:
    """Run flutter pub get."""
    log("── Running flutter pub get ──")
    flutter = find_executable("flutter")
    try:
        result = run([flutter, "pub", "get"], timeout=120)
        if result.returncode == 0:
            log("  ✓ Dependencies resolved")
            return True
        else:
            log_error("flutter pub get failed")
            log(f"  {result.stderr[-1000:]}")
            return False
    except Exception as e:
        log_error("flutter pub get exception", e)
        return False


def flutter_analyze() -> bool:
    """Run flutter analyze."""
    log("── Running flutter analyze ──")
    flutter = find_executable("flutter")
    try:
        result = run([flutter, "analyze"], timeout=180)
        if result.returncode == 0:
            log("  ✓ No analysis issues")
            return True
        else:
            log(f"  ⚠ Analysis issues:\n{result.stdout[-2000:]}")
            return True  # Don't fail for warnings in test phase
    except Exception as e:
        log_error("flutter analyze exception", e)
        return True  # Don't block


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

    try:
        result = run(cmd, timeout=600)
        if result.returncode == 0:
            build_dir = os.path.join(
                PROJECT_DIR, "build", "app", "outputs", "flutter-apk"
            )
            apk_name = f"app-{mode}.apk"
            apk_path = os.path.join(build_dir, apk_name)
            if os.path.isfile(apk_path):
                size_mb = os.path.getsize(apk_path) / (1024 * 1024)
                log(f"  ✓ APK: {apk_path} ({size_mb:.1f} MB)")
                return apk_path
            else:
                # Try to find it
                for root, dirs, files in os.walk(build_dir):
                    for f in files:
                        if f.endswith(".apk"):
                            found = os.path.join(root, f)
                            log(f"  ✓ Found APK: {found}")
                            return found
                log("  ✗ APK not found after build")
                return None
        else:
            log_error("APK build failed")
            log(f"  {result.stderr[-2000:]}")
            return None
    except Exception as e:
        log_error("APK build exception", e)
        return None


def install_and_launch(apk_path: str, device_id: str | None = None) -> bool:
    """Install APK on device and launch app."""
    log("── Installing on device ──")

    flutter = find_executable("flutter")
    cmd = [flutter, "install"]
    if device_id:
        cmd.extend(["-d", device_id])

    try:
        result = run(cmd, timeout=120)
        if result.returncode == 0:
            log("  ✓ App installed and launched")
            return True
        else:
            log_error("Install failed")
            log(f"  {result.stderr[-1000:]}")
            return False
    except Exception as e:
        log_error("Install exception", e)
        return False


def hot_reload(device_id: str | None = None) -> bool:
    """Launch `flutter run` for Hot Reload development session.

    This starts a persistent Flutter run with Hot Reload (r), Hot Restart (R),
    and other debug commands.  The user interacts through the terminal.
    Press 'q' to quit.
    """
    log("── Launching Hot Reload session ──")
    log("")
    log("  ┌─────────────────────────────────────────────┐")
    log("  │  Hot Reload Commands:                       │")
    log("  │    r  — Hot reload (inject code changes)    │")
    log("  │    R  — Hot restart (full restart)          │")
    log("  │    h  — Show all commands                   │")
    log("  │    q  — Quit                                │")
    log("  │    d  — Detach (leave app running)          │")
    log("  └─────────────────────────────────────────────┘")
    log("")

    flutter = find_executable("flutter")
    cmd = [flutter, "run", "--debug"]
    if device_id:
        cmd.extend(["-d", device_id])

    proc = run_live(cmd)

    # Persist the session
    state = load_state()
    state["last_session"] = "hot_reload"
    state["hot_reload_pid"] = proc.pid
    save_state(state)

    try:
        proc.wait()
    except KeyboardInterrupt:
        log("\n  ℹ Ctrl+C received — sending 'q' to quit Flutter…")
        try:
            proc.stdin.write("q\n")
            proc.stdin.flush()
            proc.wait(timeout=10)
        except Exception:
            proc.terminate()
            proc.wait()
    finally:
        # Clean up state
        state = load_state()
        state.pop("hot_reload_pid", None)
        save_state(state)

    return proc.returncode == 0


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="RICHY Lite — Android Build, Hot Reload & Test Script"
    )
    parser.add_argument(
        "--analyze", action="store_true",
        help="Only run static analysis",
    )
    parser.add_argument(
        "--release", action="store_true",
        help="Build release APK instead of debug",
    )
    parser.add_argument(
        "--install", action="store_true",
        help="Install and launch on connected device after build",
    )
    parser.add_argument(
        "--hot-reload", action="store_true",
        help="Launch flutter run with Hot Reload (development session)",
    )
    parser.add_argument(
        "--device", type=str, default=None,
        help="Target specific device ID (for --hot-reload or --install)",
    )
    args = parser.parse_args()

    ensure_log_dir()

    log("=" * 60)
    log("  RICHY Lite — Android Build & Test Script")
    log(f"  Platform: {platform.system()} {platform.release()}")
    log(f"  Project:  {PROJECT_DIR}")
    log(f"  Log:      {BUILD_LOG_FILE}")
    log("=" * 60)

    # ── Phase 0: Project integrity ────────────────────────────
    log("\n▶ Phase 0: Project Check")
    if not check_project_structure():
        log("\n✗ Not a valid Flutter project. Run setup_and_build.py first.")
        sys.exit(1)

    # ── Phase 1: Environment ──────────────────────────────────
    log("\n▶ Phase 1: Environment Check")

    flutter_ok = check_flutter()
    if not flutter_ok:
        log("\n✗ Cannot proceed without Flutter SDK.")
        log("  Run setup_and_build.py to auto-install Flutter & dependencies.")
        sys.exit(1)

    android_ok = check_android_sdk()
    java_ok = check_java()

    if not android_ok:
        log("\n⚠ Android SDK issues — build may fail.")
    if not java_ok:
        log("\n⚠ Java missing — build may fail.")

    devices = check_devices()

    # ── Phase 2: Dependencies ─────────────────────────────────
    log("\n▶ Phase 2: Resolve Dependencies")
    if not flutter_pub_get():
        log("\n✗ Dependency resolution failed.")
        sys.exit(1)

    # ── Phase 3: Static Analysis ──────────────────────────────
    log("\n▶ Phase 3: Static Analysis")
    flutter_analyze()

    if args.analyze:
        log("\n✓ Analysis complete (--analyze mode).")
        return

    # ── Phase 4: Hot Reload or Build ──────────────────────────
    if args.hot_reload:
        log("\n▶ Phase 4: Hot Reload Session")
        if not devices:
            log("  ⚠ No devices detected. Hot Reload requires a device/emulator.")
            log("    Start an emulator: flutter emulators --launch <id>")
            log("    Or connect a phone with USB debugging enabled.")
            sys.exit(1)
        device = args.device or devices[0]
        success = hot_reload(device)
        if not success:
            log("\n  ⚠ Hot Reload session ended with errors.")
            sys.exit(1)
        return

    log("\n▶ Phase 4: Build APK")
    apk_path = build_apk(release=args.release)
    if not apk_path:
        log("\n✗ APK build failed. Check build_logs/ for details.")
        sys.exit(1)

    # ── Phase 5: Install & Launch ─────────────────────────────
    log("\n▶ Phase 5: Install & Test")
    if (args.install or args.hot_reload) and devices:
        install_and_launch(apk_path, args.device or devices[0])
    elif args.install and not devices:
        log("  ⚠ No devices found. APK ready at:")
        log(f"    {apk_path}")
        log("  Transfer to device manually or start an emulator.")
    else:
        log(f"  ℹ APK ready: {apk_path}")
        if devices:
            log("  Run with --install to auto-install.")

    # Persist state
    state = load_state()
    state["last_build"] = datetime.now().isoformat()
    state["last_apk"] = apk_path
    save_state(state)

    log("\n" + "=" * 60)
    log("  ✓ Build complete!")
    log(f"  Build log: {BUILD_LOG_FILE}")
    log("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n  ⚠ Interrupted by user.")
        sys.exit(130)
    except Exception as e:
        log_error("Unhandled exception in build script", e)
        sys.exit(1)
