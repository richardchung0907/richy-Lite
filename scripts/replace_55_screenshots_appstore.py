#!/usr/bin/env python3
"""
Replace 5.5" Screenshots across all 10 App Store Connect Localizations
========================================================================
Deletes old 5.5" screenshots in APP_IPHONE_55 sets and uploads the newly
processed 1242x2208 PNG images across all 10 localized markets.
"""

import os
import sys
import time
import json
import hashlib
import requests
import jwt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

KEYS_FILE = "keys.txt"
KEY_P8_FILE = "AuthKey_LSLS88W574.p8"
PROCESSED_55_DIR = os.path.join("appScreenshots", "processed_55")

def load_keys():
    keys = {}
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                keys[k.strip()] = v.strip()
    return keys

def generate_jwt_token(issuer_id, key_id, p8_path):
    with open(p8_path, "r", encoding="utf-8") as f:
        private_key = f.read()
    headers = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    payload = {"iss": issuer_id, "exp": int(time.time()) + 1200, "aud": "appstoreconnect-v1"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def upload_single_screenshot(token, screenshot_set_id, file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    md5_checksum = get_file_md5(file_path)

    # 1. Asset Reservation
    url = "https://api.appstoreconnect.apple.com/v1/appScreenshots"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "data": {
            "type": "appScreenshots",
            "attributes": {"fileName": file_name, "fileSize": file_size},
            "relationships": {
                "appScreenshotSet": {
                    "data": {"type": "appScreenshotSets", "id": screenshot_set_id}
                }
            }
        }
    }

    res = requests.post(url, headers=headers, json=payload)
    if res.status_code not in [200, 201]:
        print(f"   ✗ Reservation failed for {file_name} ({res.status_code}): {res.text}")
        return False

    shot_data = res.json().get("data", {})
    shot_id = shot_data.get("id")
    upload_ops = shot_data.get("attributes", {}).get("uploadOperations", [])

    # 2. Binary Chunk Upload
    with open(file_path, "rb") as f:
        for op in upload_ops:
            op_method = op.get("method")
            op_url = op.get("url")
            op_offset = op.get("offset", 0)
            op_length = op.get("length", file_size)
            op_headers = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}

            f.seek(op_offset)
            chunk_data = f.read(op_length)

            put_res = requests.request(op_method, op_url, headers=op_headers, data=chunk_data)
            if put_res.status_code not in [200, 201, 204]:
                print(f"   ✗ Upload failed ({put_res.status_code}): {put_res.text}")
                return False

    # 3. Commit Upload
    commit_url = f"https://api.appstoreconnect.apple.com/v1/appScreenshots/{shot_id}"
    commit_payload = {
        "data": {
            "type": "appScreenshots",
            "id": shot_id,
            "attributes": {"uploaded": True, "sourceFileChecksum": md5_checksum}
        }
    }
    commit_res = requests.patch(commit_url, headers=headers, json=commit_payload)
    if commit_res.status_code in [200, 204]:
        print(f"   ✓ Uploaded 5.5\" '{file_name}' -> Asset ID: {shot_id}")
        return True
    else:
        print(f"   ✗ Commit failed for '{file_name}': {commit_res.text}")
        return False

def main():
    print("==========================================================")
    print("  Replacing 5.5\" Screenshots across 10 Localizations")
    print("==========================================================\n")

    keys = load_keys()
    token = generate_jwt_token(keys["Issuer ID for App Store Connect API"], keys["Key ID for App Store Connect API"], KEY_P8_FILE)

    app_id = "6792005935" # RICHY Lite
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Get App Store Version 1.0
    ver_r = requests.get(f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/appStoreVersions", headers=headers)
    ver_id = ver_r.json().get("data", [])[0].get("id")

    # Get Localizations
    locs_r = requests.get(f"https://api.appstoreconnect.apple.com/v1/appStoreVersions/{ver_id}/appStoreVersionLocalizations", headers=headers)
    locs = locs_r.json().get("data", [])

    screenshot_files = [os.path.join(PROCESSED_55_DIR, f) for f in os.listdir(PROCESSED_55_DIR) if f.endswith(".png")]
    screenshot_files.sort()

    print(f"Found {len(screenshot_files)} new 5.5\" PNG screenshot(s) to upload across {len(locs)} localization(s).\n")

    for loc in locs:
        loc_id = loc.get("id")
        locale = loc.get("attributes", {}).get("locale")
        print(f"Processing 5.5\" Set for Locale: '{locale}' (ID: {loc_id})")

        # Find APP_IPHONE_55 set
        ss_r = requests.get(f"https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations/{loc_id}/appScreenshotSets", headers=headers)
        ss_sets = ss_r.json().get("data", [])

        target_set_id = None
        for sset in ss_sets:
            if sset.get("attributes", {}).get("screenshotDisplayType") == "APP_IPHONE_55":
                target_set_id = sset.get("id")
                break

        if not target_set_id:
            # Create set if missing
            create_payload = {
                "data": {
                    "type": "appScreenshotSets",
                    "attributes": {"screenshotDisplayType": "APP_IPHONE_55"},
                    "relationships": {
                        "appStoreVersionLocalization": {
                            "data": {"type": "appStoreVersionLocalizations", "id": loc_id}
                        }
                    }
                }
            }
            c_res = requests.post("https://api.appstoreconnect.apple.com/v1/appScreenshotSets", headers=headers, json=create_payload)
            if c_res.status_code in [200, 201]:
                target_set_id = c_res.json().get("data", {}).get("id")
                print(f" ✓ Created APP_IPHONE_55 screenshot set (ID: {target_set_id})")
            else:
                print(f" ✗ Could not create 5.5\" screenshot set for '{locale}': {c_res.text}")
                continue

        # Delete existing screenshots in APP_IPHONE_55 set
        shots_r = requests.get(f"https://api.appstoreconnect.apple.com/v1/appScreenshotSets/{target_set_id}/appScreenshots", headers=headers)
        existing_shots = shots_r.json().get("data", []) if shots_r.status_code == 200 else []

        if existing_shots:
            print(f" Deleting {len(existing_shots)} old screenshot(s) from APP_IPHONE_55 set...")
            for s in existing_shots:
                s_id = s.get("id")
                del_res = requests.delete(f"https://api.appstoreconnect.apple.com/v1/appScreenshots/{s_id}", headers=headers)
                if del_res.status_code in [200, 204]:
                    print(f"   ✓ Deleted old screenshot {s_id}")
                else:
                    print(f"   ✗ Deletion notice ({del_res.status_code}): {del_res.text}")

        # Upload new 5.5" screenshots
        print(f" Uploading {len(screenshot_files)} new 1242x2208 PNG screenshot(s)...")
        for img_path in screenshot_files:
            upload_single_screenshot(token, target_set_id, img_path)

    print("\n==========================================================")
    print("  ✓ 5.5\" Screenshot replacement completed successfully!")
    print("==========================================================")

if __name__ == "__main__":
    main()
