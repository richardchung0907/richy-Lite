#!/usr/bin/env python3
"""
Trigger & Monitor GitHub Actions Compilation
==========================================
Pushes active code to remote origin, triggers the Android or iOS Release workflow,
polls the status of the action run every 2 minutes, and then downloads the
built release artifact (for Android) or validates TestFlight deployment (for iOS).
"""

import os
import sys
import subprocess
import time
import argparse
from datetime import datetime
import zipfile

# Decouple script location from execution directory by forcing project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

# Locate token
keys_file = "keys.txt"
if not os.path.exists(keys_file):
    print(f"Error: {keys_file} not found.")
    sys.exit(1)

token = None
with open(keys_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("Github key:"):
            token = line.split("Github key:")[1].strip()
            break

if not token:
    print("Error: Could not retrieve GitHub token from keys.txt.")
    sys.exit(1)

# Set UTF-8 printing
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ensure requests library is installed
try:
    import requests
except ImportError:
    print("Installing missing 'requests' dependency...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Git push & tag trigger
owner = "richardchung0907"
repo = "richy-Lite"

def main():
    parser = argparse.ArgumentParser(
        description="Trigger & Monitor GitHub Actions compilation and deployment pipelines."
    )
    parser.add_argument(
        "--ios", action="store_true",
        help="Build iOS & push to TestFlight instead of Android APK compilation."
    )
    args = parser.parse_args()

    platform_label = "iOS TestFlight" if args.ios else "Android APK"
    tag_suffix = "-ios" if args.ios else "-android"

    print("==========================================================")
    print(f"  RICHY Lite — {platform_label} Build Trigger & Monitoring")
    print("==========================================================\n")

    # 1. Commit any uncommitted changes first (e.g. ad_manager.dart update)
    # Check if lib/services/ad_manager.dart is actually modified
    diff_res = subprocess.run(["git", "diff", "--name-only", "lib/services/ad_manager.dart"], capture_output=True, text=True)
    if diff_res.stdout.strip():
        print("Checking for unstaged local changes in ad_manager.dart...")
        subprocess.run(["git", "add", "lib/services/ad_manager.dart"], check=True)
        commit_msg = f"chore(ad): update Appodeal App Key dynamic configuration for {platform_label}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("✓ Committed local ad manager updates successfully.")

    # 2. Get current branch and SHA
    branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    current_branch = branch_res.stdout.strip()
    sha_res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    current_sha = sha_res.stdout.strip()

    print(f"Current branch: {current_branch}")
    print(f"Current commit SHA: {current_sha}")

    # Generate unique tag to isolate pipelines and trigger the targeted Release Workflow
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag_name = f"v1.0.0-adfix-{timestamp}{tag_suffix}"
    print(f"Generating tag: {tag_name}")

    # 3. Push branch and tag using token authentication in the remote URL
    # This completely bypasses the interactive Username/Password dialog prompts.
    auth_url = f"https://{token}@github.com/{owner}/{repo}.git"

    print("Pushing current branch to origin (using token auth URL)...")
    # We redirect stderr to pipe so token doesn't leak into the output logs if a git warning triggers
    subprocess.run(["git", "push", auth_url, current_branch], check=True, stderr=subprocess.PIPE)

    print(f"Creating tag {tag_name}...")
    subprocess.run(["git", "tag", tag_name], check=True)

    print(f"Pushing tag {tag_name} to origin (using token auth URL)...")
    subprocess.run(["git", "push", auth_url, tag_name], check=True, stderr=subprocess.PIPE)

    print("✓ GitHub successfully notified of the changes and tag!")

    # 4. Monitor GitHub Actions run
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    run_id = None
    target_name_match = "iOS" if args.ios else "Android"
    print(f"Searching for the corresponding {target_name_match} Workflow Run...")
    for attempt in range(12):
        time.sleep(5)
        runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        r = requests.get(runs_url, headers=headers)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            for r_item in runs:
                # Filter by our pushed commit SHA and target platform in name
                if r_item.get("head_sha") == current_sha and target_name_match.lower() in r_item.get("name", "").lower():
                    run_id = r_item.get("id")
                    print(f"✓ Found Workflow Run ID: {run_id} ({r_item.get('name')})")
                    print(f"  Run URL: {r_item.get('html_url')}")
                    break
        if run_id:
            break
        print("  Waiting for workflow to trigger...")

    if not run_id:
        print("Error: Could not find the triggered GitHub action. Manual check may be required.")
        sys.exit(1)

    # 5. Timer loop: Check status every 2 minutes
    print("\n==========================================================")
    print("  Monitoring compilation progress (Checking every 2 minutes)")
    print("==========================================================\n")

    start_time = time.time()
    while True:
        run_detail_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
        r_detail = requests.get(run_detail_url, headers=headers)
        if r_detail.status_code == 200:
            run_data = r_detail.json()
            status = run_data.get("status")
            conclusion = run_data.get("conclusion")
            
            elapsed = int(time.time() - start_time)
            minutes, seconds = divmod(elapsed, 60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Elapsed: {minutes}m {seconds}s | Status: {status} | Conclusion: {conclusion}")
            
            if status == "completed":
                if conclusion == "success":
                    print(f"\n✓ Build compiled successfully on GitHub Actions for {platform_label}!")
                    break
                else:
                    print(f"\n✗ Build failed on GitHub Actions with conclusion: {conclusion}")
                    sys.exit(1)
        else:
            print(f"⚠ Failed to poll workflow status: {r_detail.status_code}")
        
        # Sleep 2 minutes
        time.sleep(120)

    # If it is iOS, the build has successfully been compiled and pushed to TestFlight
    if args.ios:
        print(f"\n==========================================================")
        print(f"  🎉 SUCCESS! iOS build compiled and pushed to TestFlight.")
        print(f"  Please open Apple TestFlight on your device to test.")
        print(f"==========================================================")
        return

    # 6. Fetch artifacts and download (Android only)
    print("\nRetrieving build artifacts...")
    artifacts_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
    art_r = requests.get(artifacts_url, headers=headers)
    if art_r.status_code != 200:
        print(f"Error fetching artifacts (Status: {art_r.status_code})")
        sys.exit(1)

    artifacts = art_r.json().get("artifacts", [])
    apk_art = None
    for art in artifacts:
        if art.get("name") == "android-apk-release":
            apk_art = art
            break

    if not apk_art:
        print("Error: Could not find artifact 'android-apk-release'.")
        sys.exit(1)

    download_url = apk_art.get("archive_download_url")
    print(f"✓ Found APK Artifact: {apk_art.get('name')} ({apk_art.get('size_in_bytes')} bytes)")
    print("Downloading artifact ZIP...")

    # Create target directory
    artifacts_dir = "build_artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    zip_path = os.path.join(artifacts_dir, "android-apk-release.zip")

    zip_r = requests.get(download_url, headers=headers, stream=True)
    if zip_r.status_code == 200:
        with open(zip_path, "wb") as f_zip:
            for chunk in zip_r.iter_content(chunk_size=128*1024):
                f_zip.write(chunk)
        print(f"✓ Downloaded ZIP successfully to {zip_path}")
    else:
        print(f"Error downloading ZIP (Status: {zip_r.status_code})")
        sys.exit(1)

    # Extract APK from zip
    print("Extracting app-release.apk...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(artifacts_dir)

    # Check if app-release.apk exists
    apk_final_path = os.path.join(artifacts_dir, "app-release.apk")
    if os.path.exists(apk_final_path):
        # Clean up the zip file
        os.remove(zip_path)
        print(f"\n==========================================================")
        print(f"  🎉 SUCCESS! APK is downloaded and available locally:")
        print(f"  {os.path.abspath(apk_final_path)}")
        print(f"==========================================================")
    else:
        print("Error: app-release.apk was not extracted properly.")
        sys.exit(1)

if __name__ == "__main__":
    main()
