#!/usr/bin/env python3
"""
RICHY Lite — Launch Emulator & Hot Reload
==========================================
One-command script to:
  1. Check for port conflicts, stale ADB daemons, and running emulators
  2. Resolve conflicts (kill stale processes, restart ADB)
  3. Launch the RichyTest Android emulator
  4. Build and install the latest APK
  5. Start flutter run with Hot Reload

Usage:
    python scripts/run_app.py              # Full flow: check → launch → build → run
    python scripts/run_app.py --only-build # Build APK only (no emulator, no run)
    python scripts/run_app.py --only-run   # Skip build, just launch & hot reload
    python scripts/run_app.py --cold       # Cold start emulator (wipe data)
"""

import argparse
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

# ── Paths & Setup ──────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

LOG_DIR = os.path.join(PROJECT_DIR, "build_logs")
LOG_FILE = os.path.join(LOG_DIR, f"run_{datetime.now():%Y%m%d_%H%M%S}.log")
EMULATOR_NAME = "RichyTest"

# ADB port (default)
ADB_PORT = 5037
# Emulator console ports (first two instances)
EMULATOR_PORTS = [5554, 5555]


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    ensure_log_dir()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def find_exe(name: str) -> str | None:
    exe = shutil.which(name)
    if exe:
        return exe
    # Flutter fallback
    if platform.system() == "Windows":
        flutter_paths = [
            os.path.expandvars(r"%USERPROFILE%\flutter\bin\flutter.bat"),
            r"C:\flutter\bin\flutter.bat",
            r"C:\src\flutter\bin\flutter.bat",
        ]
        for p in flutter_paths:
            if os.path.isfile(p):
                return p
    return None


def find_adb() -> str | None:
    """Find ADB executable."""
    adb = shutil.which("adb")
    if adb:
        return adb
    android_home = os.environ.get("ANDROID_HOME", "")
    if android_home:
        adb_path = os.path.join(android_home, "platform-tools", "adb")
        if platform.system() == "Windows":
            adb_path += ".exe"
        if os.path.isfile(adb_path):
            return adb_path
    # Fallback
    default = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
    if os.path.isfile(default):
        return default
    return None


# ── Phase 1: Conflict Detection & Resolution ─────────────────────


def kill_adb():
    """Kill the ADB server to clean up stale connections."""
    adb = find_adb()
    if not adb:
        return
    log("  Killing ADB server…")
    try:
        subprocess.run([adb, "kill-server"], timeout=15, capture_output=True)
        time.sleep(1)
        log("  ✓ ADB server killed")
    except Exception as e:
        log(f"  ⚠ {e}")


def check_port_conflicts() -> bool:
    """Check if ADB or emulator ports are in use by other processes."""
    log("── Checking port conflicts ──")
    conflicts = False

    # Check ADB port
    for port in [ADB_PORT] + EMULATOR_PORTS:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True, text=True, timeout=10,
                )
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        pid = line.strip().split()[-1]
                        log(f"  ⚠ Port {port} in use by PID {pid}")
                        conflicts = True
            else:
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.stdout.strip():
                    log(f"  ⚠ Port {port} in use")
                    conflicts = True
        except Exception:
            pass

    if not conflicts:
        log("  ✓ No port conflicts")
    return conflicts


def check_running_emulators() -> list[str]:
    """Return list of running emulator serials."""
    adb = find_adb()
    if not adb:
        return []

    try:
        result = subprocess.run(
            [adb, "devices"], timeout=15,
            capture_output=True, text=True,
        )
        devices = []
        for line in result.stdout.splitlines()[1:]:
            if line.strip() and "device" in line:
                serial = line.split("\t")[0]
                if serial.startswith("emulator-"):
                    devices.append(serial)
        return devices
    except Exception:
        return []


def resolve_conflicts():
    """Kill stale processes and reset ADB if needed."""
    log("── Resolving conflicts ──")

    running = check_running_emulators()
    if running:
        log(f"  Found running emulators: {running}")
        log("  ℹ Reusing existing emulator(s) — no conflict resolution needed")
        return

    # Only kill ADB if no emulators are running
    if check_port_conflicts():
        log("  Resolving port conflicts: restarting ADB…")
        kill_adb()
        # Start ADB fresh
        adb = find_adb()
        if adb:
            subprocess.run([adb, "start-server"], timeout=15, capture_output=True)
            log("  ✓ ADB restarted")
    else:
        # Ensure ADB is running
        adb = find_adb()
        if adb:
            subprocess.run([adb, "start-server"], timeout=15, capture_output=True)
        log("  ✓ No conflicts to resolve")


# ── Phase 2: Emulator Launch ─────────────────────────────────────


def launch_emulator(cold: bool = False) -> bool:
    """Launch the RichyTest emulator. Returns True if ready."""
    log(f"── Launching emulator: {EMULATOR_NAME} ──")

    # Check if already running
    running = check_running_emulators()
    if running:
        log(f"  ✓ Emulator already running: {running[0]}")
        # Wait for boot complete
        _wait_for_boot(running[0])
        return True

    flutter = find_exe("flutter")
    if not flutter:
        log("  ✗ Flutter not found")
        return False

    # Launch emulator
    cmd = [flutter, "emulators", "--launch", EMULATOR_NAME]
    if cold:
        # Cold boot: wipe user data
        emulator_exe = _find_emulator_exe()
        if emulator_exe:
            log("  Cold boot: wiping user data…")
            subprocess.Popen(
                [emulator_exe, "-avd", EMULATOR_NAME, "-wipe-data", "-no-boot-anim"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            time.sleep(3)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    log("  Waiting for emulator to boot…")
    # Wait for device to appear
    for i in range(60):
        time.sleep(3)
        devices = check_running_emulators()
        if devices:
            log(f"  ✓ Emulator connected: {devices[0]}")
            _wait_for_boot(devices[0])
            return True
        if i % 5 == 0:
            log(f"    Still waiting… ({i * 3}s)")

    log("  ✗ Emulator failed to boot within 3 minutes")
    return False


def _find_emulator_exe() -> str | None:
    android_home = os.environ.get("ANDROID_HOME", "")
    if not android_home:
        android_home = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk")
    emu = os.path.join(android_home, "emulator", "emulator.exe")
    if os.path.isfile(emu):
        return emu
    return None


def _wait_for_boot(serial: str):
    """Wait for emulator boot to complete."""
    adb = find_adb()
    if not adb:
        return
    log("  Waiting for boot completion…")
    for i in range(40):
        try:
            result = subprocess.run(
                [adb, "-s", serial, "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True, timeout=10,
            )
            if result.stdout.strip() == "1":
                log("  ✓ Boot complete")
                # Wait for package manager
                time.sleep(3)
                return
        except Exception:
            pass
        time.sleep(2)
    log("  ⚠ Boot completion check timed out")


# ── Phase 3: Build & Install ─────────────────────────────────────


def build_and_install() -> bool:
    """Build debug APK and install on connected device."""
    log("── Building APK ──")

    flutter = find_exe("flutter")
    if not flutter:
        log("  ✗ Flutter not found")
        return False

    # Check project
    main_dart = os.path.join(PROJECT_DIR, "lib", "main.dart")
    if not os.path.isfile(main_dart):
        log("  ✗ lib/main.dart not found — not a Flutter project")
        return False

    # Build
    result = subprocess.run(
        [flutter, "build", "apk", "--debug"],
        cwd=PROJECT_DIR, timeout=600,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        log(f"  ✗ Build failed:\n{result.stderr[-1000:]}")
        return False

    log("  ✓ APK built")

    # Find APK
    apk = os.path.join(PROJECT_DIR, "build", "app", "outputs", "flutter-apk", "app-debug.apk")
    if not os.path.isfile(apk):
        log("  ✗ APK not found")
        return False

    # Install
    devices = check_running_emulators()
    if not devices:
        log("  ✗ No device to install to")
        return False

    adb = find_adb()
    result = subprocess.run(
        [adb, "-s", devices[0], "install", "-r", apk],
        timeout=120, capture_output=True, text=True,
    )
    if "Success" in result.stdout:
        log("  ✓ Installed")
        return True
    else:
        log(f"  ✗ Install failed: {result.stdout.strip()}")
        return False


# ── Phase 4: Hot Reload ──────────────────────────────────────────


def start_hot_reload():
    """Launch flutter run with Hot Reload."""
    log("── Starting Hot Reload session ──")
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

    import threading

    flutter = find_exe("flutter")
    devices = check_running_emulators()
    device_arg = ["-d", devices[0]] if devices else []

    log(f"  LIVE: flutter run {' '.join(device_arg)}")
    proc = subprocess.Popen(
        [flutter, "run", "--debug"] + device_arg,
        cwd=PROJECT_DIR,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
    )

    def input_bridge():
        try:
            while proc.poll() is None:
                line = sys.stdin.readline()
                if not line:
                    break
                if proc.poll() is None and proc.stdin:
                    proc.stdin.write(line)
                    proc.stdin.flush()
        except Exception:
            pass

    bridge_thread = threading.Thread(target=input_bridge, daemon=True)
    bridge_thread.start()

    try:
        proc.wait()
    except KeyboardInterrupt:
        log("\n  ℹ Ctrl+C detected. Forcibly terminating Flutter process...")
        try:
            proc.kill()
            proc.wait()
        except Exception:
            pass
        log("  ✓ Terminated.")


# ── Main ─────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="RICHY Lite — Launch Emulator & Hot Reload"
    )
    parser.add_argument(
        "--only-build", action="store_true",
        help="Build APK only (no emulator, no run)",
    )
    parser.add_argument(
        "--only-run", action="store_true",
        help="Skip build, just launch emulator & hot reload",
    )
    parser.add_argument(
        "--cold", action="store_true",
        help="Cold start emulator (wipe user data)",
    )
    args = parser.parse_args()

    ensure_log_dir()

    log("=" * 60)
    log("  RICHY Lite — Launch & Hot Reload")
    log(f"  Platform: {platform.system()} {platform.release()}")
    log(f"  Project:  {PROJECT_DIR}")
    log(f"  Log:      {LOG_FILE}")
    log("=" * 60)

    # ── Phase 1: Conflict Resolution ──────────────────────────
    log("\n▶ Phase 1: Conflict Check & Resolution")
    resolve_conflicts()

    # ── Phase 2: Emulator ─────────────────────────────────────
    if not args.only_build:
        log("\n▶ Phase 2: Emulator Launch")
        if not launch_emulator(cold=args.cold):
            sys.exit(1)

    # ── Phase 3: Build & Install ──────────────────────────────
    if not args.only_run:
        log("\n▶ Phase 3: Build & Install")
        if not build_and_install():
            sys.exit(1)

    if args.only_build:
        log("\n✓ Build complete.")
        return

    # ── Phase 4: Hot Reload ───────────────────────────────────
    log("\n▶ Phase 4: Hot Reload")
    start_hot_reload()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n  ⚠ Interrupted by user.")
        sys.exit(130)
    except Exception as e:
        log(f"  ✗ Unhandled: {e}")
        sys.exit(1)
