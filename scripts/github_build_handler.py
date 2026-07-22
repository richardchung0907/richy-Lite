#!/usr/bin/env python3
"""
Trigger & Monitor GitHub Actions Compilation
==========================================
Pushes active code to remote origin, triggers the Android Release workflow,
polls the status of the action run every 2 minutes, and then downloads the
built release artifact, extracting 'app-release.apk' locally.
"""

import os
import sys
import subprocess
import time
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

# 1. Get current branch and SHA
branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
current_branch = branch_res.stdout.strip()
sha_res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
current_sha = sha_res.stdout.strip()

print(f"Current branch: {current_branch}")
print(f"Current commit SHA: {current_sha}")

# Generate unique tag with -android suffix to isolate pipelines and prevent triggering iOS Release Workflows
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
tag_name = f"v1.0.0-adfix-{timestamp}-android"
print(f"Generating tag: {tag_name}")

# 2. Push branch and tag using token authentication in the remote URL
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

# 3. Monitor GitHub Actions run
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

run_id = None
print("Searching for the corresponding Workflow Run...")
for attempt in range(12):
    time.sleep(5)
    runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    r = requests.get(runs_url, headers=headers)
    if r.status_code == 200:
        runs = r.json().get("workflow_runs", [])
        for r_item in runs:
            # We filter by our pushed commit SHA
            if r_item.get("head_sha") == current_sha and "Android" in r_item.get("name", ""):
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

# 4. Timer loop: Check status every 2 minutes
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
                print("\n✓ Build compiled successfully on GitHub Actions!")
                break
            else:
                print(f"\n✗ Build failed on GitHub Actions with conclusion: {conclusion}")
                sys.exit(1)
    else:
        print(f"⚠ Failed to poll workflow status: {r_detail.status_code}")
    
    # Sleep 2 minutes
    time.sleep(120)

# 5. Fetch artifacts and download
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
