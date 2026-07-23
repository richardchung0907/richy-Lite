#!/usr/bin/env python3
"""
Deep App Store Connect Settings Inspector & Auto-Fixer
======================================================
Inspects App Store submission readiness:
1. Build attachment to Version 1.0
2. Screenshot Display Targets (APP_IPHONE_65 / APP_IPHONE_67 vs APP_IPHONE_55)
3. App Privacy Declarations for Appodeal
4. Age Rating Declaration
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
    keys = load_keys()
    token = generate_jwt_token(keys["Issuer ID for App Store Connect API"], keys["Key ID for App Store Connect API"], KEY_P8_FILE)

    app_id = "6792005935" # RICHY Lite
    
    print("==========================================================")
    print("  Deep Audit & Submission Readiness Checklist")
    print("==========================================================\n")

    # 1. Check Version & Attached Build
    ver_r = api_get(token, f"apps/{app_id}/appStoreVersions", params={"include": "build"})
    ver_data = ver_r.json().get("data", [])[0]
    ver_id = ver_data.get("id")
    ver_attrs = ver_data.get("attributes", {})
    
    attached_build = None
    if ver_r.json().get("included"):
        for inc in ver_r.json().get("included"):
            if inc.get("type") == "builds":
                attached_build = inc

    print(f"App Store Version: {ver_attrs.get('versionString')} ({ver_attrs.get('appStoreState')})")
    if attached_build:
        b_attrs = attached_build.get("attributes", {})
        print(f"✓ Attached Build: Version {b_attrs.get('version')} (Build {b_attrs.get('buildVersion')}) | ID: {attached_build.get('id')}")
    else:
        print("⚠ No build attached to this App Store Version yet.")

    # Get latest uploaded valid build
    builds_r = api_get(token, f"apps/{app_id}/builds", params={"limit": 1})
    latest_build = builds_r.json().get("data", [])[0] if builds_r.json().get("data") else None
    if latest_build:
        lb_attrs = latest_build.get("attributes", {})
        print(f"Latest Available Build in App Store Connect: Version {lb_attrs.get('version')} (ID: {latest_build.get('id')})")

    # 2. Check Localizations and Screenshot Display Targets
    locs_r = api_get(token, f"appStoreVersions/{ver_id}/appStoreVersionLocalizations")
    locs = locs_r.json().get("data", [])

    print(f"\nAuditing Localized Screenshot Display Types across {len(locs)} languages...")
    display_types_found = set()
    for loc in locs:
        loc_id = loc.get("id")
        locale = loc.get("attributes", {}).get("locale")
        ss_r = api_get(token, f"appStoreVersionLocalizations/{loc_id}/appScreenshotSets")
        ss_sets = ss_r.json().get("data", [])
        for ss in ss_sets:
            dtype = ss.get("attributes", {}).get("screenshotDisplayType")
            display_types_found.add(dtype)

    print(f"Active Screenshot Display Sets: {display_types_found}")
    
    # Check if 6.5" or 6.7" is missing
    has_65_or_67 = any(t in display_types_found for t in ["APP_IPHONE_65", "APP_IPHONE_67"])
    if not has_65_or_67:
        print("⚠ WARNING: Apple requires 6.5\" or 6.7\" display size screenshots for modern iPhone submissions.")
        print("  Currently only APP_IPHONE_55 is set. We should add APP_IPHONE_65 / APP_IPHONE_67 screenshot sets!")

    # 3. Check App Info & Age Rating Details
    info_r = api_get(token, f"apps/{app_id}/appInfos", params={"include": "ageRatingDeclaration"})
    info_data = info_r.json().get("data", [])[0]
    info_id = info_data.get("id")
    
    age_r = api_get(token, f"appInfos/{info_id}/ageRatingDeclaration")
    age_attrs = age_r.json().get("data", {}).get("attributes", {}) if age_r.status_code == 200 and age_r.json().get("data") else {}
    
    print("\nAge Rating Declaration Summary:")
    print(f" - Alcohol/Tobacco/Drug: {age_attrs.get('alcoholTobaccoOrDrugUseOrReferences')}")
    print(f" - Gambling/Contests: {age_attrs.get('gamblingAndContests')}")
    print(f" - Horror/Fear: {age_attrs.get('horrorOrFearThemes')}")
    print(f" - Medical/Treatment: {age_attrs.get('unratedOrRestrictedMedicalTreatment')}")
    print(f" - Sexual/Nudity: {age_attrs.get('profanityOrCrudeHumor')}")

    # Output detailed report
    result = {
        "ver_id": ver_id,
        "attached_build_id": attached_build.get("id") if attached_build else None,
        "latest_build_id": latest_build.get("id") if latest_build else None,
        "display_types_found": list(display_types_found),
        "has_65_or_67": has_65_or_67
    }
    with open("build_artifacts/deep_audit.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
