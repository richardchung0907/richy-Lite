#!/usr/bin/env python3
"""
Deploy Latest Release APK to Emulator (with GUI Window)
======================================================
Imports and leverages run_app.py, but forces Windows cmd shell "start" command
to spawn the RichyTest emulator in the interactive desktop session so the user
can see the emulator GUI window.
"""

import os
import sys
import time
import subprocess

# Locate directory structures
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

# Force path inserts so it can find run_app inside its sibling dir scripts/
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Set UTF-8 printing
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import the sibling run_app helpers to reuse robust logic
import run_app

def launch_emulator_with_window(cold: bool = False) -> bool:
    """Launch the RichyTest emulator with interactive GUI window on Windows."""
    run_app.log(f"── Launching emulator with GUI window: {run_app.EMULATOR_NAME} ──")

    # Check if already running
    running = run_app.check_running_emulators()
    if running:
        run_app.log(f"  ✓ Emulator already running: {running[0]}")
        run_app._wait_for_boot(running[0])
        return True

    emulator_exe = run_app._find_emulator_exe()
    if not emulator_exe:
        android_home = os.environ.get("ANDROID_HOME", "")
        if not android_home:
            android_home = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk")
        emulator_exe = os.path.join(android_home, "emulator", "emulator.exe")

    if not os.path.isfile(emulator_exe):
        run_app.log("  ✗ emulator.exe not found")
        return False

    # Spawning with 'start' on Windows guarantees interactive GUI window in active user session!
    args = ["-avd", run_app.EMULATOR_NAME]
    if cold:
        args += ["-wipe-data"]
    
    run_app.log(f"  Launching via cmd 'start' to show GUI window...")
    cmd = f'start "" "{emulator_exe}" ' + ' '.join(args)
    subprocess.Popen(cmd, shell=True)

    run_app.log("  Waiting for emulator to boot…")
    # Wait for device to appear
    for i in range(60):
        time.sleep(3)
        devices = run_app.check_running_emulators()
        if devices:
            run_app.log(f"  ✓ Emulator connected: {devices[0]}")
            run_app._wait_for_boot(devices[0])
            return True
        if i % 5 == 0:
            run_app.log(f"    Still waiting… ({i * 3}s)")

    run_app.log("  ✗ Emulator failed to boot within 3 minutes")
    return False

def main():
    run_app.ensure_log_dir()
    run_app.log("="*60)
    run_app.log(" Deploying Latest Release APK to RichyTest Emulator")
    run_app.log("="*60)
    
    # 1. Resolve conflicts
    run_app.log("\n[Step 1] Resolve Conflicts")
    run_app.resolve_conflicts()
    
    # 2. Launch emulator (with GUI window)
    run_app.log("\n[Step 2] Launch Emulator")
    if not launch_emulator_with_window():
        run_app.log("x Failed to launch emulator")
        sys.exit(1)
        
    # 3. Find and Install the latest release APK
    run_app.log("\n[Step 3] Install Release APK")
    apk_path = os.path.join("build_artifacts", "app-release.apk")
    if not os.path.isfile(apk_path):
        run_app.log(f"x Release APK not found at {apk_path}")
        sys.exit(1)
        
    devices = run_app.check_running_emulators()
    if not devices:
        run_app.log("x No running emulators found")
        sys.exit(1)
        
    adb = run_app.find_adb()
    if not adb:
        run_app.log("x ADB not found")
        sys.exit(1)
        
    package_name = "com.richylite.richyLite"
    
    # Proactively uninstall the existing package to resolve signature mismatch failures
    run_app.log(f"Proactively uninstalling existing {package_name} if present to prevent signature mismatch...")
    subprocess.run([adb, "-s", devices[0], "uninstall", package_name], capture_output=True)
    
    run_app.log(f"Installing {apk_path} on {devices[0]}...")
    result = subprocess.run(
        [adb, "-s", devices[0], "install", "-r", apk_path],
        capture_output=True, text=True
    )
    if "Success" in result.stdout or result.returncode == 0:
        run_app.log("v Successfully installed release APK!")
        
        # 4. Start the app on the emulator
        run_app.log("\n[Step 4] Starting the App")
        subprocess.run(
            [adb, "-s", devices[0], "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"],
            capture_output=True
        )
        run_app.log("v App started successfully on emulator!")
    else:
        run_app.log(f"x Install failed:\nStdout: {result.stdout}\nStderr: {result.stderr}")
        sys.exit(1)

if __name__ == '__main__':
    main()
