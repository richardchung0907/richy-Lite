#!/usr/bin/env python3
"""
Appodeal API Audit and Configuration Tool
=========================================
Uses official Appodeal REST API (Applications API & Reporting API) to inspect
and update application settings on the Appodeal backend.

Official API Endpoints:
  - Applications API: POST https://api-services.appodeal.com/api/v2/apps
  - Reporting/Stats API: GET https://api-services.appodeal.com/api/v2/stats_api
  - Status Polling API: GET https://api-services.appodeal.com/api/v2/check_status
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timedelta

# Decouple script location from execution directory by forcing project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

# Fix Windows console UTF-8 printing
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

KEYS_FILE = "keys.txt"

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

def main():
    print("==========================================================")
    print("  RICHY Lite — Official Appodeal REST API Audit & Manager")
    print("==========================================================\n")

    keys = load_keys()
    api_key = keys.get("Appodeal API key")
    user_id = keys.get("Appodeal User ID")
    android_app_key = keys.get("Appodeal App key(Android)")
    ios_app_key = keys.get("Appodeal App key(ios)")

    print(f"Loaded API Key: {api_key[:6]}...{api_key[-4:] if api_key else ''}")
    print(f"Loaded User ID: {user_id}")
    print(f"Loaded Android App Key: {android_app_key}")
    print(f"Loaded iOS App Key: {ios_app_key}\n")

    audit_results = {
        "timestamp": datetime.now().isoformat(),
        "official_api_endpoints_used": {
            "apps_api": "POST https://api-services.appodeal.com/api/v2/apps",
            "stats_api": "GET https://api-services.appodeal.com/api/v2/stats_api"
        },
        "rate_limiting_timer_seconds": 2.0,
        "android_app_status": {},
        "ios_app_status": {},
        "stats_api_status": {}
    }

    apps_url = "https://api-services.appodeal.com/api/v2/apps"
    stats_url = "https://api-services.appodeal.com/api/v2/stats_api"

    # -------------------------------------------------------------------
    # Step 1: Query & Update Android Application Settings via Official API
    # -------------------------------------------------------------------
    print("[1] Inspecting & Updating Android App Settings via Official Applications API...")
    payload_android = {
        "api_key": api_key,
        "user_id": user_id,
        "app_key": android_app_key,
        "name": "RICHY Lite",
        "orientation": "portrait",
        "coppa": 0,
        "is_for_kids": 0,
        "filter_mature_content": 0,
        "is_game": 0
    }

    try:
        r_android = requests.post(apps_url, json=payload_android, timeout=10)
        print(f"-> Status: {r_android.status_code}")
        print(f"-> Response: {r_android.text}")
        if r_android.status_code == 200:
            res_json = r_android.json()
            audit_results["android_app_status"] = res_json
            print(f"✓ Android App Backend Configuration Updated Successfully!")
    except Exception as e:
        print(f"✗ Exception updating Android App: {e}")
        audit_results["android_app_status"]["error"] = str(e)

    # Enforce Rate Limiting Delay
    print("-> Enforcing 2.0s rate-limiting timer delay...")
    time.sleep(2.0)

    # -------------------------------------------------------------------
    # Step 2: Query & Update iOS Application Settings via Official API
    # -------------------------------------------------------------------
    print("\n[2] Inspecting & Updating iOS App Settings via Official Applications API...")
    payload_ios = {
        "api_key": api_key,
        "user_id": user_id,
        "app_key": ios_app_key,
        "name": "RICHY Lite",
        "orientation": "portrait",
        "coppa": 0,
        "is_for_kids": 0,
        "filter_mature_content": 0,
        "is_game": 0
    }

    try:
        r_ios = requests.post(apps_url, json=payload_ios, timeout=10)
        print(f"-> Status: {r_ios.status_code}")
        print(f"-> Response: {r_ios.text}")
        if r_ios.status_code == 200:
            res_json = r_ios.json()
            audit_results["ios_app_status"] = res_json
            print(f"✓ iOS App Backend Configuration Updated Successfully!")
    except Exception as e:
        print(f"✗ Exception updating iOS App: {e}")
        audit_results["ios_app_status"]["error"] = str(e)

    # Enforce Rate Limiting Delay
    print("-> Enforcing 2.0s rate-limiting timer delay...")
    time.sleep(2.0)

    # -------------------------------------------------------------------
    # Step 3: Trigger & Test Reporting / Stats API
    # -------------------------------------------------------------------
    print("\n[3] Querying Appodeal Reporting / Stats API...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_str = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    params_stats = {
        "api_key": api_key,
        "user_id": user_id,
        "date_from": start_str,
        "date_to": today_str
    }

    try:
        r_stats = requests.get(stats_url, params=params_stats, timeout=10)
        print(f"-> Status: {r_stats.status_code}")
        print(f"-> Response: {r_stats.text}")
        if r_stats.status_code == 200:
            s_json = r_stats.json()
            audit_results["stats_api_status"] = s_json
            print(f"✓ Stats API Triggered Successfully (Task ID: {s_json.get('task_id')})!")
    except Exception as e:
        print(f"✗ Exception querying Stats API: {e}")
        audit_results["stats_api_status"]["error"] = str(e)

    # Save detailed JSON output to docs/appodeal_api_audit_results.json
    out_dir = os.path.join(PROJECT_DIR, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "appodeal_api_audit_results.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Audit & Configuration Results saved to: {out_file}")
    print("==========================================================")

if __name__ == "__main__":
    main()
