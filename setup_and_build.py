#!/usr/bin/env python3
"""
RICHY Lite — One-Click Environment Setup, Build & Test
========================================================
Master script that automates the ENTIRE pipeline from a clean
Windows 10 machine:

  1. Checks Windows version
  2. Downloads & installs Flutter SDK
  3. Downloads & installs all build dependencies
  4. Configures environment (PATH, ANDROID_HOME, JAVA_HOME)
  5. Runs `flutter doctor` to verify
  6. Runs build_android.py to compile
  7. Launches the app on device/emulator

On **subsequent** runs, it detects existing installations and asks
whether to rebuild, start Hot Reload, or just quit.

Usage:
    python setup_and_build.py              # Full auto-setup + build
    python setup_and_build.py --fresh      # Force re-install everything
    python setup_and_build.py --check-only # Only check environment
    python setup_and_build.py --hot-reload # Skip to Hot Reload directly
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPTS_DIR  # same directory

SETUP_LOG_DIR = os.path.join(PROJECT_DIR, "build_logs")
SETUP_LOG_FILE = os.path.join(
    SETUP_LOG_DIR,
    f"setup_{datetime.now():%Y%m%d_%H%M%S}.log",
)
STATE_FILE = os.path.join(SETUP_LOG_DIR, ".setup_state.json")

# Default install locations
FLUTTER_ROOT_DEFAULT = os.path.expandvars(r"%USERPROFILE%\flutter")
ANDROID_SDK_DEFAULT = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk")
JAVA_DEFAULT = os.path.expandvars(r"%PROGRAMFILES%\Eclipse Adoptium\jdk-17.0.12.7-hotspot")

# ── Logging ────────────────────────────────────────────────────────


def ensure_log_dir():
    os.makedirs(SETUP_LOG_DIR, exist_ok=True)


def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    ensure_log_dir()
    try:
        with open(SETUP_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def log_error(msg: str, exc: Optional[Exception] = None):
    log(f"  ✗ ERROR: {msg}")
    if exc:
        for line in "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).splitlines():
            log(f"    {line}")


# ── State Management ───────────────────────────────────────────────


def load_state() -> dict:
    if os.path.isfile(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict):
    ensure_log_dir()
    state["last_updated"] = datetime.now().isoformat()
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except OSError:
        pass


# ── Cleanup ─────────────────────────────────────────────────────────


def cleanup_leftovers():
    """Remove leftover temp files from previous failed runs.

    Call at startup so a failed run doesn't pollute TEMP or leave
    half-installed SDKs that block re-installation.
    """
    log("── Cleaning up leftover temp files ──")
    cleaned = 0

    # Temp zip archives
    for fname in ["flutter_stable.zip", "jdk17_windows.zip", "android_cmdline.zip"]:
        path = os.path.join(tempfile.gettempdir(), fname)
        if os.path.isfile(path):
            try:
                os.remove(path)
                log(f"  Removed leftover: {path}")
                cleaned += 1
            except OSError:
                pass

    # Temp extraction dir
    extract_dir = os.path.join(tempfile.gettempdir(), "android_cmdline_extract")
    if os.path.isdir(extract_dir):
        try:
            shutil.rmtree(extract_dir, ignore_errors=True)
            log(f"  Removed leftover: {extract_dir}")
            cleaned += 1
        except OSError:
            pass

    if cleaned == 0:
        log("  ✓ Nothing to clean up")
    return cleaned


# ── Subprocess Helpers ─────────────────────────────────────────────


def run_cmd(
    cmd: list[str],
    cwd: str | None = None,
    timeout: int = 300,
    capture: bool = True,
    allow_timeout: bool = False,
) -> subprocess.CompletedProcess | None:
    """Run a command, return CompletedProcess (or None if timeout and allowed).

    Uses UTF-8 encoding to handle Flutter's Unicode output on Windows.
    When `allow_timeout=True`, returns None instead of raising on timeout.
    """
    log(f"  RUN: {' '.join(cmd)}")
    env = os.environ.copy()
    # Force UTF-8 for subprocess I/O on Windows
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        return subprocess.run(
            cmd,
            cwd=cwd or PROJECT_DIR,
            capture_output=capture,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=(platform.system() == "Windows") and capture,
            env=env,
        )
    except subprocess.TimeoutExpired:
        if allow_timeout:
            log(f"  ⚠ Timeout after {timeout}s (non-fatal)")
            return None
        log(f"  ✗ Timeout after {timeout}s")
        raise
    except Exception as e:
        log_error(f"Command failed: {' '.join(cmd)}", e)
        raise


def find_exe(name: str) -> str | None:
    """Find executable on PATH or common locations."""
    exe = shutil.which(name)
    if exe:
        return exe
    if platform.system() == "Windows":
        # Common Flutter paths
        for p in [
            os.path.join(FLUTTER_ROOT_DEFAULT, "bin", "flutter.bat"),
            os.path.expandvars(r"%LOCALAPPDATA%\flutter\bin\flutter.bat"),
            r"C:\flutter\bin\flutter.bat",
            r"C:\src\flutter\bin\flutter.bat",
        ]:
            if os.path.isfile(p):
                return p
        # ADB fallback: check ANDROID_HOME\platform-tools
        if name in ("adb", "adb.exe"):
            android_home = os.environ.get("ANDROID_HOME", "") or os.environ.get("ANDROID_SDK_ROOT", "")
            if android_home:
                adb_path = os.path.join(android_home, "platform-tools", "adb.exe")
                if os.path.isfile(adb_path):
                    return adb_path
            # Also check default location
            default_adb = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
            if os.path.isfile(default_adb):
                return default_adb
    return None


def refresh_env():
    """Re-read environment variables (helps after PATH modifications)."""
    # On Windows, environment changes in registry are picked up by new shells
    # but not the current process. We try our best.
    if platform.system() == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ,
            )
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    os.environ[name] = value
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass

        # Also system env
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                0,
                winreg.KEY_READ,
            )
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    if name not in os.environ:
                        os.environ[name] = value
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass


def set_user_env_var(name: str, value: str):
    """Set a persistent user environment variable on Windows."""
    if platform.system() != "Windows":
        log(f"  ℹ setx not available — manually export {name}={value}")
        os.environ[name] = value
        return

    try:
        result = run_cmd(["setx", name, value], timeout=30)
        if result.returncode == 0:
            os.environ[name] = value
            log(f"  ✓ Set {name}={value}")
        else:
            log(f"  ⚠ setx failed: {result.stderr.strip()}")
    except Exception:
        log(f"  ⚠ Could not set {name} — add manually to System Environment Variables.")


def add_to_path(new_path: str):
    """Append a directory to the user PATH."""
    current = os.environ.get("PATH", "")
    if new_path in current:
        return
    new_paths = current + ";" + new_path if current else new_path
    set_user_env_var("PATH", new_paths)


# ── Windows Version Check ──────────────────────────────────────────


def check_windows() -> bool:
    """Verify we are on Windows 10+."""
    log("── Checking Windows Version ──")
    if platform.system() != "Windows":
        log("  ✗ This script is designed for Windows 10/11.")
        return False

    ver = platform.version()
    log(f"  ✓ Windows {platform.release()} (build {ver})")

    # Windows 10 build >= 10240, Windows 11 build >= 22000
    try:
        build = int(ver.split(".")[2]) if len(ver.split(".")) > 2 else 0
        if build < 10240:
            log("  ⚠ Windows version may be too old. Recommend Windows 10+.")
    except (ValueError, IndexError):
        pass
    return True


# ── Download Helper ────────────────────────────────────────────────


def download_file(url: str, dest: str, desc: str = "", sha256: str = "") -> bool:
    """Download a file with progress indicator and optional SHA256 verification."""
    log(f"  Downloading {desc or url} …")
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "RICHY-Lite-Setup/1.0"})
        with urllib.request.urlopen(req, timeout=600) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 8192
            hasher = hashlib.sha256()
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)
                    if total > 0 and downloaded % (block_size * 128) == 0:
                        pct = downloaded * 100 // total
                        sys.stdout.write(f"\r    {pct}% …")
                        sys.stdout.flush()
            if total > 0:
                sys.stdout.write("\r    100%  \n")
                sys.stdout.flush()

        # SHA256 verification
        if sha256:
            actual_hash = hasher.hexdigest()
            if actual_hash.lower() != sha256.lower():
                log(f"  ✗ SHA256 mismatch!")
                log(f"    Expected: {sha256}")
                log(f"    Got:      {actual_hash}")
                os.remove(dest)
                return False
            log(f"  ✓ SHA256 verified")

        log(f"  ✓ Downloaded to {dest}")
        return True
    except Exception as e:
        log_error(f"Download failed: {url}", e)
        # Clean up partial download
        try:
            if os.path.isfile(dest):
                os.remove(dest)
        except OSError:
            pass
        return False


# ── Flutter Installation ───────────────────────────────────────────


FLUTTER_STABLE_URL = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.44.5-stable.zip"
FLUTTER_STABLE_SHA256 = "64ff1f561e0811bc724d597f9fe6faa6b3e74b11c02c320076fbbe239a717a11"


def get_flutter_url() -> str:
    """Return the Flutter download URL. Uses a well-known stable version."""
    return FLUTTER_STABLE_URL


def install_flutter(force: bool = False) -> bool:
    """Download and install Flutter SDK."""
    log("── Installing Flutter SDK ──")

    flutter_exe = os.path.join(FLUTTER_ROOT_DEFAULT, "bin", "flutter.bat")
    if os.path.isfile(flutter_exe) and not force:
        log(f"  ✓ Flutter already present at {FLUTTER_ROOT_DEFAULT}")
        add_to_path(os.path.join(FLUTTER_ROOT_DEFAULT, "bin"))
        refresh_env()
        # Quick verification to confirm it's not a broken install
        flutter = find_exe("flutter")
        if flutter:
            result = run_cmd([flutter, "--version"], timeout=120, capture=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "Flutter" in line and ("channel" in line or chr(8226) in line or "•" in line or "-" in line):
                        log(f"  ✓ {line.strip()}")
                        break
                state = load_state()
                state["flutter_installed"] = True
                state["flutter_root"] = FLUTTER_ROOT_DEFAULT
                save_state(state)
                return True
            else:
                log("  ⚠ Existing Flutter failed verification. Re-installing…")
        else:
            log("  ⚠ Flutter binary not found on PATH. Re-installing…")

    url = get_flutter_url()
    zip_path = os.path.join(tempfile.gettempdir(), "flutter_stable.zip")

    if not os.path.isfile(zip_path) or force:
        if not download_file(url, zip_path, "Flutter SDK", sha256=FLUTTER_STABLE_SHA256):
            return False

    log("  Extracting Flutter SDK …")
    try:
        # Remove existing if force
        if force and os.path.isdir(FLUTTER_ROOT_DEFAULT):
            shutil.rmtree(FLUTTER_ROOT_DEFAULT, ignore_errors=True)
        os.makedirs(os.path.dirname(FLUTTER_ROOT_DEFAULT), exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(os.path.dirname(FLUTTER_ROOT_DEFAULT))
        log(f"  ✓ Extracted to {FLUTTER_ROOT_DEFAULT}")

        # Add to PATH
        flutter_bin = os.path.join(FLUTTER_ROOT_DEFAULT, "bin")
        add_to_path(flutter_bin)
        refresh_env()

        # Verify
        flutter = find_exe("flutter")
        if flutter:
            result = run_cmd([flutter, "--version"], timeout=120)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "Flutter" in line and ("channel" in line or "•" in line):
                        log(f"  ✓ {line.strip()}")
                        break
                state = load_state()
                state["flutter_installed"] = True
                state["flutter_root"] = FLUTTER_ROOT_DEFAULT
                save_state(state)
                return True
            else:
                log(f"  ✗ flutter --version returned code {result.returncode}")
        log("  ✗ Flutter installation verification failed.")
        log(f"    Removing broken install at {FLUTTER_ROOT_DEFAULT} …")
        try:
            shutil.rmtree(FLUTTER_ROOT_DEFAULT, ignore_errors=True)
            log("    ✓ Removed.")
        except OSError:
            log("    ⚠ Could not remove. Please delete manually.")
        return False
    except Exception as e:
        log_error("Flutter installation failed", e)
        return False
    finally:
        # Clean up zip
        try:
            os.remove(zip_path)
        except OSError:
            pass


# ── Java JDK Installation ──────────────────────────────────────────


JDK17_URL = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip"


def install_java(force: bool = False) -> bool:
    """Download and install JDK 17."""
    log("── Installing Java JDK 17 ──")

    # Check if already installed
    java_exe = find_exe("java")
    if java_exe and not force:
        result = run_cmd([java_exe, "-version"], timeout=30)
        ver_line = result.stderr.splitlines()[0] if result.stderr else ""
        if "17" in ver_line or "21" in ver_line:
            log(f"  ✓ Java already installed: {ver_line}")
            state = load_state()
            state["java_installed"] = True
            state["java_path"] = java_exe
            save_state(state)
            return True

    zip_path = os.path.join(tempfile.gettempdir(), "jdk17_windows.zip")
    if not os.path.isfile(zip_path) or force:
        if not download_file(JDK17_URL, zip_path, "JDK 17"):
            return False

    log("  Extracting JDK …")
    install_dir = os.path.expandvars(r"%PROGRAMFILES%\Eclipse Adoptium")
    try:
        os.makedirs(install_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(install_dir)

        # Find the extracted directory
        for item in os.listdir(install_dir):
            full = os.path.join(install_dir, item)
            if os.path.isdir(full) and "jdk" in item.lower():
                jdk_home = full
                break
        else:
            log("  ✗ Could not locate JDK directory after extraction.")
            return False

        log(f"  ✓ JDK installed to {jdk_home}")
        set_user_env_var("JAVA_HOME", jdk_home)
        add_to_path(os.path.join(jdk_home, "bin"))
        refresh_env()

        state = load_state()
        state["java_installed"] = True
        state["java_home"] = jdk_home
        save_state(state)
        return True
    except Exception as e:
        log_error("JDK installation failed", e)
        return False
    finally:
        try:
            os.remove(zip_path)
        except OSError:
            pass


# ── Android SDK Installation ───────────────────────────────────────


ANDROID_CMDLINE_URL = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"


def install_android_sdk(force: bool = False) -> bool:
    """Download Android command-line tools and install required SDK packages."""
    log("── Installing Android SDK ──")

    # Check if already present
    sdkmanager = os.path.join(ANDROID_SDK_DEFAULT, "cmdline-tools", "latest", "bin", "sdkmanager.bat")
    if os.path.isfile(sdkmanager) and not force:
        log(f"  ✓ Android SDK already at {ANDROID_SDK_DEFAULT}")
        return True

    zip_path = os.path.join(tempfile.gettempdir(), "android_cmdline.zip")
    if not os.path.isfile(zip_path) or force:
        if not download_file(ANDROID_CMDLINE_URL, zip_path, "Android CMD Tools"):
            return False

    log("  Extracting Android command-line tools …")
    tools_dir = os.path.join(ANDROID_SDK_DEFAULT, "cmdline-tools", "latest")
    os.makedirs(tools_dir, exist_ok=True)

    try:
        # The zip has a top-level "cmdline-tools" folder; extract into a temp dir
        tmp_extract = os.path.join(tempfile.gettempdir(), "android_cmdline_extract")
        if os.path.isdir(tmp_extract):
            shutil.rmtree(tmp_extract, ignore_errors=True)
        os.makedirs(tmp_extract, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_extract)

        # The zip contains: cmdline-tools/bin/, cmdline-tools/lib/, etc.
        src = os.path.join(tmp_extract, "cmdline-tools")
        if not os.path.isdir(src):
            # Some versions extract differently — try to find
            for item in os.listdir(tmp_extract):
                p = os.path.join(tmp_extract, item)
                if os.path.isdir(p):
                    src = p
                    break

        # Move contents to tools_dir
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(tools_dir, item)
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
            elif os.path.isfile(d):
                os.remove(d)
            shutil.move(s, d)
        shutil.rmtree(tmp_extract, ignore_errors=True)

        log(f"  ✓ CMD tools installed to {tools_dir}")

        # Set environment
        set_user_env_var("ANDROID_HOME", ANDROID_SDK_DEFAULT)
        os.environ["ANDROID_HOME"] = ANDROID_SDK_DEFAULT
        refresh_env()

        # Accept licenses (non-interactive: pipe 'y' answers via stdin)
        log("  Accepting Android SDK licenses …")
        sdkmanager = os.path.join(tools_dir, "bin", "sdkmanager.bat")
        if os.path.isfile(sdkmanager):
            log("  RUN: (echo y | sdkmanager --licenses)")
            try:
                subprocess.run(
                    f'echo y | "{sdkmanager}" --licenses',
                    cwd=PROJECT_DIR,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                    shell=True,
                )
                log("  ✓ Licenses accepted")
            except subprocess.TimeoutExpired:
                log("  ⚠ License acceptance timed out (may already be accepted)")
            except Exception as e:
                log_error("License acceptance failed", e)

            # Install essential packages
            log("  Installing SDK packages (platform-tools, build-tools, platform) …")
            packages = [
                "platform-tools",
                "build-tools;34.0.0",
                "platforms;android-34",
                "emulator",
                "system-images;android-34;google_apis;x86_64",
            ]
            run_cmd(
                [sdkmanager] + packages,
                timeout=600,
            )
            log("  ✓ SDK packages installed")

        state = load_state()
        state["android_sdk_installed"] = True
        state["android_home"] = ANDROID_SDK_DEFAULT
        save_state(state)
        return True
    except Exception as e:
        log_error("Android SDK installation failed", e)
        return False
    finally:
        try:
            os.remove(zip_path)
        except OSError:
            pass
        # Clean temp
        tmp_extract = os.path.join(tempfile.gettempdir(), "android_cmdline_extract")
        if os.path.isdir(tmp_extract):
            shutil.rmtree(tmp_extract, ignore_errors=True)


# ── Git Check ──────────────────────────────────────────────────────


def check_git() -> bool:
    """Check Git is installed (needed by Flutter)."""
    log("── Checking Git ──")
    git = find_exe("git")
    if git:
        result = run_cmd([git, "--version"], timeout=30)
        log(f"  ✓ {result.stdout.strip()}")
        return True
    else:
        log("  ✗ Git not found. Install from https://git-scm.com/download/win")
        return False


# ── Flutter Doctor ─────────────────────────────────────────────────


def run_flutter_doctor() -> bool:
    """Run flutter doctor to verify the setup."""
    log("── Running flutter doctor ──")
    flutter = find_exe("flutter")
    if not flutter:
        log("  ✗ Flutter not found")
        return False

    result = run_cmd([flutter, "doctor"], timeout=180)
    if result.returncode == 0:
        log("  ✓ flutter doctor passed")
        return True
    else:
        log(f"  ⚠ flutter doctor found issues:\n{result.stdout[-2000:]}")
        # Don't fail; doctor is informational
        return True


# ── Flutter Project Bootstrap ─────────────────────────────────────


def _ensure_android_resources():
    """Create missing Android resource files that Flutter plugins require.

    Some plugins (e.g., share_plus, image_picker) need res/xml/file_paths.xml
    for FileProvider. If it's missing, AAPT linking fails.
    """
    res_xml = os.path.join(PROJECT_DIR, "android", "app", "src", "main", "res", "xml")
    file_paths_xml = os.path.join(res_xml, "file_paths.xml")
    if not os.path.isfile(file_paths_xml):
        os.makedirs(res_xml, exist_ok=True)
        with open(file_paths_xml, "w") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<paths>\n')
            f.write('    <cache-path name="cache" path="." />\n')
            f.write('    <external-cache-path name="external_cache" path="." />\n')
            f.write('    <root-path name="root" path="." />\n')
            f.write('</paths>\n')
        log("  ✓ Created missing android/app/src/main/res/xml/file_paths.xml")


def ensure_flutter_project() -> bool:
    """Create the Flutter project if it doesn't exist yet."""
    log("── Ensuring Flutter Project ──")

    main_dart = os.path.join(PROJECT_DIR, "lib", "main.dart")
    if os.path.isfile(main_dart):
        log("  ✓ Flutter project already exists (lib/main.dart found)")
        # Ensure required Android resources exist (may be missing in manual setup)
        _ensure_android_resources()
        return True

    log("  Creating Flutter project…")
    flutter = find_exe("flutter")
    if not flutter:
        log("  ✗ Flutter not available")
        return False

    result = run_cmd([
        flutter, "create",
        "--project-name", "richy_lite",
        "--org", "com.richylite",
        "--platforms", "android,ios",
        ".",
    ], timeout=120)
    if result.returncode == 0:
        log("  ✓ Flutter project created")
        return True
    else:
        log_error("flutter create failed")
        log(f"  {result.stderr[-1000:]}")
        return False


# ── Environment Summary ────────────────────────────────────────────


def print_summary(devices: list[str]):
    """Print a summary of the current environment."""
    log("")
    log("  ┌─────────────────────────────────────────────┐")
    log("  │         Environment Summary                  │")
    log(f"  │  Flutter  : {'✓' if find_exe('flutter') else '✗'}                             │")
    log(f"  │  Git      : {'✓' if find_exe('git') else '✗'}                             │")
    log(f"  │  Java     : {'✓' if find_exe('java') else '✗'}                             │")
    log(f"  │  Devices  : {len(devices)} connected                        │")
    log("  └─────────────────────────────────────────────┘")
    log("")


# ── Interactive Menu ──────────────────────────────────────────────


def show_menu() -> str:
    """Display interactive menu for subsequent runs. Returns choice."""
    print()
    print("  ┌──────────────────────────────────────────┐")
    print("  │  RICHY Lite — Already Configured!        │")
    print("  │                                          │")
    print("  │  [1] Rebuild APK + Install & Run         │")
    print("  │  [2] Hot Reload (development session)    │")
    print("  │  [3] Rebuild APK only (no install)       │")
    print("  │  [4] Run flutter doctor (diagnostics)    │")
    print("  │  [5] Fresh re-install everything         │")
    print("  │  [q] Quit                                │")
    print("  └──────────────────────────────────────────┘")
    print()

    while True:
        choice = input("  Enter choice [1-5/q]: ").strip().lower()
        if choice in ("1", "2", "3", "4", "5", "q"):
            return choice
        print("  Invalid choice. Try again.")


# ── Main Pipeline ─────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="RICHY Lite — One-Click Setup, Build & Test"
    )
    parser.add_argument(
        "--fresh", action="store_true",
        help="Force re-install all dependencies",
    )
    parser.add_argument(
        "--check-only", action="store_true",
        help="Only check environment, don't install or build",
    )
    parser.add_argument(
        "--hot-reload", action="store_true",
        help="Skip to Hot Reload session directly",
    )
    parser.add_argument(
        "--no-interactive", action="store_true",
        help="Run non-interactively (no menu, auto-build)",
    )
    args = parser.parse_args()

    ensure_log_dir()

    log("=" * 60)
    log("  RICHY Lite — One-Click Setup & Build")
    log(f"  Platform: {platform.system()} {platform.release()}")
    log(f"  Project:  {PROJECT_DIR}")
    log(f"  Log:      {SETUP_LOG_FILE}")
    log("=" * 60)

    # ── Phase 0: Cleanup leftovers from previous failed runs ────
    cleanup_leftovers()

    # ── Phase 0: Platform Check ────────────────────────────────
    log("\n▶ Phase 0: Platform Check")
    if not check_windows():
        sys.exit(1)

    check_git()  # warn but don't fail

    # ── Phase 1: Detect existing setup ─────────────────────────
    state = load_state()
    already_setup = all([
        state.get("flutter_installed"),
        state.get("java_installed"),
        state.get("android_sdk_installed"),
    ])

    if already_setup and not args.fresh:
        log("\n  ✓ Environment already configured from previous run.")
        log(f"    Last setup: {state.get('last_updated', 'unknown')}")

        if args.check_only:
            run_flutter_doctor()
            return

        if args.hot_reload:
            # Skip to hot reload
            pass  # will be handled below
        elif args.no_interactive:
            log("  Auto-building (--no-interactive)…")
            pass  # fall through to build
        else:
            choice = show_menu()
            if choice == "q":
                log("  Goodbye! 👋")
                return
            elif choice == "5":
                args.fresh = True
                # fall through to full install
            elif choice == "4":
                run_flutter_doctor()
                return
            elif choice == "2":
                args.hot_reload = True
                # fall through to check and hot reload
            elif choice == "3":
                args.check_only = False
                # build only, no install — handled via build_android.py
            # choice 1: build + install (default path)

    # ── Phase 2: Install Dependencies ──────────────────────────
    log("\n▶ Phase 2: Install Dependencies")

    # Flutter
    if not install_flutter(force=args.fresh):
        log("\n✗ Flutter installation failed. Cannot continue.")
        sys.exit(1)
    refresh_env()

    # Java
    if not install_java(force=args.fresh):
        log("\n⚠ Java installation failed. Build may fail.")

    # Android SDK
    if not install_android_sdk(force=args.fresh):
        log("\n⚠ Android SDK installation failed. Build may fail.")

    # Refresh environment one more time
    refresh_env()

    # ── Phase 3: Verify ────────────────────────────────────────
    log("\n▶ Phase 3: Verify Setup")
    run_flutter_doctor()

    # ── Phase 4: Project Bootstrap ─────────────────────────────
    log("\n▶ Phase 4: Project Bootstrap")
    ensure_flutter_project()

    if args.check_only:
        log("\n✓ Environment check complete (--check-only).")
        return

    # ── Phase 5: Build / Hot Reload ────────────────────────────
    log("\n▶ Phase 5: Build & Test")

    # Check for devices (robust: start ADB server first, non-fatal on timeout)
    adb = find_exe("adb")
    devices = []
    if adb:
        # Ensure ADB daemon is running before querying devices
        run_cmd([adb, "start-server"], timeout=30, allow_timeout=True)
        result = run_cmd([adb, "devices"], timeout=60, allow_timeout=True)
        if result and result.returncode == 0:
            for line in result.stdout.splitlines()[1:]:
                if line.strip() and "\tdevice" in line:
                    devices.append(line.split("\t")[0])
        elif result is None:
            log("  ⚠ adb devices timed out — continuing without device detection")

    print_summary(devices)

    build_script = os.path.join(PROJECT_DIR, "build_android.py")

    if args.hot_reload:
        if not devices:
            log("  ⚠ No devices connected. Hot Reload needs a device/emulator.")
            log("    Start an emulator: flutter emulators --launch <id>")
            sys.exit(1)

        cmd = [sys.executable, build_script, "--clean", "--hot-reload"]
        if devices:
            cmd.extend(["--device", devices[0]])
        log(f"  Launching Hot Reload…")
        subprocess.run(cmd, cwd=PROJECT_DIR)
    else:
        # Build APK
        cmd = [sys.executable, build_script, "--clean"]
        if args.fresh:
            cmd.append("--release")
        result = subprocess.run(cmd, cwd=PROJECT_DIR)
        if result.returncode != 0:
            log("\n✗ Build failed.")
            sys.exit(1)

        # Install and launch
        if devices:
            log("\n  Installing on device…")
            install_cmd = [sys.executable, build_script, "--install", "--device", devices[0]]
            subprocess.run(install_cmd, cwd=PROJECT_DIR)

    # ── Done ───────────────────────────────────────────────────
    state = load_state()
    state["last_run"] = datetime.now().isoformat()
    save_state(state)

    log("\n" + "=" * 60)
    log("  ✓ All done!")
    log(f"  Setup log: {SETUP_LOG_FILE}")
    log("  Next time, just run: python setup_and_build.py")
    log("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n  ⚠ Interrupted by user.")
        sys.exit(130)
    except Exception as e:
        log_error("Unhandled exception in setup script", e)
        sys.exit(1)
