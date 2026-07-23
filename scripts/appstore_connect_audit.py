#!/usr/bin/env python3
"""
App Store Connect API Audit & Setup Utility
===========================================
Queries App Store Connect REST API using JWT (ES256) to inspect, audit,
and configure app metadata, categories, age ratings, privacy declarations,
localized strings, URLs, screenshots, and TestFlight builds.
"""

import os
import sys
import time
import json
import requests
import jwt

# Bootstrap project directory
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
    if not os.path.exists(KEYS_FILE):
        print(f"Error: {KEYS_FILE} not found.")
        sys.exit(1)
    
    keys = {}
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                keys[k.strip()] = v.strip()
    return keys

def generate_jwt_token(issuer_id, key_id, p8_path):
    if not os.path.exists(p8_path):
        print(f"Error: Private key file {p8_path} not found.")
        sys.exit(1)
        
    with open(p8_path, "r", encoding="utf-8") as f:
        private_key = f.read()

    headers = {
        "alg": "ES256",
        "kid": key_id,
        "typ": "JWT"
    }

    payload = {
        "iss": issuer_id,
        "exp": int(time.time()) + 1200, # 20 minutes
        "aud": "appstoreconnect-v1"
    }

    token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return token

def api_get(token, endpoint, params=None):
    url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.get(url, headers=headers, params=params)
    return r

def api_patch(token, endpoint, payload):
    url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.patch(url, headers=headers, json=payload)
    return r

def api_post(token, endpoint, payload):
    url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json=payload)
    return r

def main():
    print("==========================================================")
    print("  RICHY Lite — App Store Connect API Comprehensive Audit  ")
    print("==========================================================\n")

    keys = load_keys()
    issuer_id = keys.get("Issuer ID for App Store Connect API")
    key_id = keys.get("Key ID for App Store Connect API")

    if not issuer_id or not key_id:
        print("Error: Missing Issuer ID or Key ID in keys.txt")
        sys.exit(1)

    print(f"Issuer ID: {issuer_id}")
    print(f"Key ID:    {key_id}")
    
    token = generate_jwt_token(issuer_id, key_id, KEY_P8_FILE)
    print("✓ Successfully generated App Store Connect JWT auth token.")

    os.makedirs("build_artifacts", exist_ok=True)

    # 1. Get List of Apps
    print("\n[1. Fetching Apps list from App Store Connect...]")
    r = api_get(token, "apps", params={"include": "appInfos,appStoreVersions,builds"})
    if r.status_code != 200:
        print(f"Failed to fetch apps list (Status: {r.status_code}): {r.text}")
        sys.exit(1)

    data = r.json()
    apps = data.get("data", [])
    print(f"Found {len(apps)} app(s) in this developer account.")

    target_app = None
    for app in apps:
        attrs = app.get("attributes", {})
        print(f" - App ID: {app.get('id')} | Name: '{attrs.get('name')}' | Bundle ID: '{attrs.get('bundleId')}' | SKU: '{attrs.get('sku')}'")
        if attrs.get("bundleId") == "com.richylite.richyLite" or "richy" in attrs.get("name", "").lower():
            target_app = app

    if not target_app and apps:
        target_app = apps[0]

    if not target_app:
        print("\n⚠ No app found in App Store Connect with bundle ID 'com.richylite.richyLite'.")
        return

    app_id = target_app.get("id")
    app_attrs = target_app.get("attributes", {})
    print(f"\nTarget App Selected: '{app_attrs.get('name')}' (ID: {app_id}, Bundle ID: {app_attrs.get('bundleId')})")

    # 2. Detailed Audit of App Info
    print("\n[2. Auditing App Info & Categories...]")
    app_info_r = api_get(token, f"apps/{app_id}/appInfos", params={"include": "primaryCategory,secondaryCategory,ageRatingDeclaration"})
    app_infos = app_info_r.json().get("data", []) if app_info_r.status_code == 200 else []
    
    for info in app_infos:
        info_id = info.get("id")
        info_attrs = info.get("attributes", {})
        print(f" - AppInfo ID: {info_id} | App Store State: {info_attrs.get('appStoreState')}")
        
        # Check Categories
        cat_r = api_get(token, f"appInfos/{info_id}/primaryCategory")
        primary_cat = cat_r.json().get("data", {}).get("id") if cat_r.status_code == 200 else "None"
        sec_cat_r = api_get(token, f"appInfos/{info_id}/secondaryCategory")
        secondary_cat = sec_cat_r.json().get("data", {}).get("id") if sec_cat_r.status_code == 200 else "None"
        
        print(f"   Primary Category:   {primary_cat}")
        print(f"   Secondary Category: {secondary_cat}")

        # Check Age Rating
        age_r = api_get(token, f"appInfos/{info_id}/ageRatingDeclaration")
        if age_r.status_code == 200 and age_r.json().get("data"):
            age_data = age_r.json().get("data", {}).get("attributes", {})
            print(f"   Age Rating Declaration found. Kids Age Band: {age_data.get('kidsAgeBand')}")
        else:
            print("   Age Rating Declaration: Not configured yet.")

    # 3. Check App Store Versions & Localizations
    print("\n[3. Auditing App Store Versions & Metadata...]")
    ver_r = api_get(token, f"apps/{app_id}/appStoreVersions", params={"include": "appStoreVersionLocalizations,build"})
    versions = ver_r.json().get("data", []) if ver_r.status_code == 200 else []
    
    for ver in versions:
        ver_id = ver.get("id")
        ver_attrs = ver.get("attributes", {})
        print(f" - Version String: {ver_attrs.get('versionString')} | Platform: {ver_attrs.get('platform')} | State: {ver_attrs.get('appStoreState')}")
        
        locs_r = api_get(token, f"appStoreVersions/{ver_id}/appStoreVersionLocalizations")
        locs = locs_r.json().get("data", []) if locs_r.status_code == 200 else []
        for loc in locs:
            loc_id = loc.get("id")
            loc_attrs = loc.get("attributes", {})
            print(f"   Localization ({loc_attrs.get('locale')}):")
            print(f"     Description:     '{loc_attrs.get('description', '')[:60]}...'")
            print(f"     Keywords:        '{loc_attrs.get('keywords', '')}'")
            print(f"     Support URL:     '{loc_attrs.get('supportUrl', '')}'")
            print(f"     Marketing URL:   '{loc_attrs.get('marketingUrl', '')}'")
            print(f"     Promotional Text:'{loc_attrs.get('promotionalText', '')}'")

            # Check Screenshots
            ss_r = api_get(token, f"appStoreVersionLocalizations/{loc_id}/appScreenshotSets")
            ss_sets = ss_r.json().get("data", []) if ss_r.status_code == 200 else []
            print(f"     Screenshot Sets: {len(ss_sets)} display size set(s) uploaded.")
            for ss_set in ss_sets:
                ss_attrs = ss_set.get("attributes", {})
                ss_items_r = api_get(token, f"appScreenshotSets/{ss_set.get('id')}/appScreenshots")
                ss_count = len(ss_items_r.json().get("data", [])) if ss_items_r.status_code == 200 else 0
                print(f"       Display Target: {ss_attrs.get('screenshotDisplayType')} -> {ss_count} screenshot(s)")

    # 4. Check Builds / TestFlight Status
    print("\n[4. Auditing Builds & TestFlight Status...]")
    builds_r = api_get(token, f"apps/{app_id}/builds", params={"limit": 5})
    builds = builds_r.json().get("data", []) if builds_r.status_code == 200 else []
    print(f"Found {len(builds)} uploaded build(s).")
    for b in builds:
        b_attrs = b.get("attributes", {})
        print(f" - Version {b_attrs.get('version')} (Build {b_attrs.get('buildVersion')}) | Uploaded: {b_attrs.get('uploadedDate')} | Processing: {b_attrs.get('processingState')}")

    # Output complete audit JSON summary to file for analysis
    audit_summary = {
        "app": target_app,
        "app_infos": app_infos,
        "versions": versions,
        "builds_count": len(builds)
    }
    with open("build_artifacts/appstore_connect_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2, ensure_ascii=False)

    print("\n==========================================================")
    print("  ✓ App Store Connect audit complete!")
    print("    Full diagnostic stored in build_artifacts/appstore_connect_audit.json")
    print("==========================================================")

if __name__ == "__main__":
    main()
