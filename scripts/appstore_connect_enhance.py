#!/usr/bin/env python3
"""
App Store Connect Enhancer & Optimizer
======================================
1. Creates APP_IPHONE_65 (6.5" Display) Screenshot Sets for all 10 localized languages in App Store Connect.
2. Attaches the latest valid build to App Store Version 1.0.
"""

import os
import sys
import time
import json
import requests
import jwt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

# Fix Windows console UTF-8 printing
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

KEYS_FILE = "keys.txt"
KEY_P8_FILE = "AuthKey_LSLS88W574.p8"

def load_keys():
    keys = {}
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                k, v = line.split(":", 1)
                keys[k.strip()] = v.strip()
    return keys

def generate_jwt_token(issuer_id, key_id, p8_path):
    with open(p8_path, "r", encoding="utf-8") as f:
        private_key = f.read()
    headers = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    payload = {"iss": issuer_id, "exp": int(time.time()) + 1200, "aud": "appstoreconnect-v1"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

def api_get(token, endpoint, params=None):
    url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.get(url, headers=headers, params=params)

def api_patch(token, endpoint, payload):
    url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.patch(url, headers=headers, json=payload)

def api_post(token, endpoint, payload):
    url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, headers=headers, json=payload)

def main():
    print("==========================================================")
    print("  RICHY Lite — App Store Connect Enhancer & Optimizer    ")
    print("==========================================================\n")

    keys = load_keys()
    token = generate_jwt_token(keys["Issuer ID for App Store Connect API"], keys["Key ID for App Store Connect API"], KEY_P8_FILE)

    app_id = "6792005935" # RICHY Lite

    # 1. Fetch App Store Version 1.0
    ver_r = api_get(token, f"apps/{app_id}/appStoreVersions")
    ver_data = ver_r.json().get("data", [])[0]
    ver_id = ver_data.get("id")
    print(f"Targeting App Store Version ID: {ver_id} (Version {ver_data.get('attributes', {}).get('versionString')})")

    # 2. Add APP_IPHONE_65 Screenshot Sets for all 10 localizations
    locs_r = api_get(token, f"appStoreVersions/{ver_id}/appStoreVersionLocalizations")
    locs = locs_r.json().get("data", [])

    print(f"\n[1. Creating APP_IPHONE_65 Screenshot Sets for {len(locs)} Localizations...]")
    for loc in locs:
        loc_id = loc.get("id")
        locale = loc.get("attributes", {}).get("locale")
        
        # Check existing sets
        ss_r = api_get(token, f"appStoreVersionLocalizations/{loc_id}/appScreenshotSets")
        ss_sets = ss_r.json().get("data", [])
        existing_types = [s.get("attributes", {}).get("screenshotDisplayType") for s in ss_sets]
        
        if "APP_IPHONE_65" not in existing_types:
            payload = {
                "data": {
                    "type": "appScreenshotSets",
                    "attributes": {
                        "screenshotDisplayType": "APP_IPHONE_65"
                    },
                    "relationships": {
                        "appStoreVersionLocalization": {
                            "data": {
                                "type": "appStoreVersionLocalizations",
                                "id": loc_id
                            }
                        }
                    }
                }
            }
            res = api_post(token, "appScreenshotSets", payload)
            if res.status_code in [200, 201]:
                print(f" ✓ Created APP_IPHONE_65 screenshot set for locale '{locale}'")
            else:
                print(f" ✗ Failed to create APP_IPHONE_65 set for locale '{locale}' ({res.status_code}): {res.text}")
        else:
            print(f" ✓ Locale '{locale}' already has APP_IPHONE_65 set.")

    # 3. Attach latest valid build (if available) to Version 1.0
    print("\n[2. Checking build attachment for Version 1.0...]")
    builds_r = api_get(token, f"apps/{app_id}/builds", params={"limit": 5})
    builds = builds_r.json().get("data", [])
    
    valid_build = None
    for b in builds:
        if b.get("attributes", {}).get("processingState") == "VALID":
            valid_build = b
            break

    if valid_build:
        build_id = valid_build.get("id")
        build_ver = valid_build.get("attributes", {}).get("version")
        print(f"Found latest valid build ID: {build_id} (Version: {build_ver})")
        
        # Attach build to App Store Version
        attach_payload = {
            "data": {
                "type": "appStoreVersions",
                "id": ver_id,
                "relationships": {
                    "build": {
                        "data": {
                            "type": "builds",
                            "id": build_id
                        }
                    }
                }
            }
        }
        att_res = api_patch(token, f"appStoreVersions/{ver_id}", attach_payload)
        if att_res.status_code in [200, 204]:
            print(f" ✓ Successfully attached Build {build_ver} (ID: {build_id}) to App Store Version 1.0!")
        else:
            print(f" Notice on attach build ({att_res.status_code}): {att_res.text}")
    else:
        print(" No valid build found to attach.")

    print("\n==========================================================")
    print("  ✓ App Store Connect enhancements completed successfully!")
    print("==========================================================")

if __name__ == "__main__":
    main()
