#!/usr/bin/env python3
"""
Appodeal API Audit and Configuration Tool
=========================================
Systematically inspects and attempts modifications to Appodeal app settings,
placements, mediation waterfalls, and account configurations using the Appodeal REST API.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def test_single_endpoint(item):
    base, method, ep, payload, headers, api_key, user_id, idx = item
    target_url = f"{base}{ep}"
    params = {"api_key": api_key, "user_id": str(user_id)}
    
    try:
        if method == "GET":
            r = requests.get(target_url, headers=headers, params=params, timeout=5)
        elif method == "PUT":
            r = requests.put(target_url, headers=headers, json=payload, params=params, timeout=5)
        elif method == "PATCH":
            r = requests.patch(target_url, headers=headers, json=payload, params=params, timeout=5)
        elif method == "POST":
            r = requests.post(target_url, headers=headers, json=payload, params=params, timeout=5)
        elif method == "DELETE":
            r = requests.delete(target_url, headers=headers, params=params, timeout=5)
        else:
            return None

        return {
            "url": target_url,
            "method": method,
            "header_variant": idx + 1,
            "status_code": r.status_code,
            "response_preview": r.text[:200].replace("\n", " ")
        }
    except Exception as e:
        return {
            "url": target_url,
            "method": method,
            "header_variant": idx + 1,
            "error": str(e)
        }

def main():
    print("==========================================================")
    print("  RICHY Lite — Appodeal API Audit & Management Utility")
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
        "stats_api_test": {},
        "management_api_attempts": [],
        "summary": {}
    }

    # -------------------------------------------------------------------
    # Step 1: Query Reporting / Stats API (Official Supported API)
    # -------------------------------------------------------------------
    print("[1] Testing Appodeal Reporting / Stats API...")
    stats_url = "https://api-services.appodeal.com/api/v2/stats_api"
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_str = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    params = {
        "api_key": api_key,
        "user_id": user_id,
        "date_from": start_str,
        "date_to": today_str
    }

    try:
        r = requests.get(stats_url, params=params, timeout=10)
        print(f"-> Request URL: {r.url}")
        print(f"-> Response Code: {r.status_code}")
        print(f"-> Response Text: {r.text[:300]}")

        audit_results["stats_api_test"]["trigger_status"] = r.status_code
        audit_results["stats_api_test"]["trigger_response"] = r.text

        if r.status_code == 200:
            res_data = r.json()
            task_id = res_data.get("task_id")
            if task_id:
                print(f"-> Received Task ID: {task_id}. Polling check_status API...")
                check_url = "https://api-services.appodeal.com/api/v2/check_status"
                for i in range(5):
                    time.sleep(2)
                    cr = requests.get(check_url, params={"api_key": api_key, "user_id": user_id, "task_id": task_id}, timeout=10)
                    print(f"   Poll #{i+1}: Status {cr.status_code} | Text: {cr.text[:200]}")
                    if cr.status_code == 200:
                        cdata = cr.json()
                        audit_results["stats_api_test"]["completed_data"] = cdata
                        if cdata.get("status") == 1 or cdata.get("task_status") == "1":
                            print(f"✓ Task Status verified!")
                            break
    except Exception as e:
        print(f"✗ Stats API Exception: {e}")
        audit_results["stats_api_test"]["exception"] = str(e)

    print("\n----------------------------------------------------------\n")

    # -------------------------------------------------------------------
    # Step 2: Parallel Testing of Management / Modification API Endpoints
    # -------------------------------------------------------------------
    print("[2] Systematically Testing Appodeal Dashboard/App Management API Endpoints...")

    headers_options = [
        {"api-key": api_key, "user-id": str(user_id), "Content-Type": "application/json"},
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {"X-Api-Key": api_key, "Content-Type": "application/json"}
    ]

    base_urls = [
        "https://api-services.appodeal.com/api/v2",
        "https://api-services.appodeal.com/api/v1",
        "https://api.appodeal.com/api/v2",
        "https://api.appodeal.com/api/v1",
        "https://appodeal.com/api/v2",
        "https://www.appodeal.com/api/v2"
    ]

    endpoints_to_test = [
        # Listing Apps & Account Information
        ("GET", "/apps", None),
        ("GET", f"/apps/{android_app_key}", None),
        ("GET", f"/apps/{ios_app_key}", None),
        ("GET", "/placements", None),
        ("GET", f"/apps/{android_app_key}/placements", None),
        ("GET", f"/apps/{ios_app_key}/placements", None),
        ("GET", f"/apps/{android_app_key}/ad_units", None),
        ("GET", f"/apps/{android_app_key}/waterfall", None),
        ("GET", "/account", None),
        ("GET", "/user", None),

        # Modifying / Updating App & Placement Configurations (POST/PUT/PATCH/DELETE)
        ("PUT", f"/apps/{android_app_key}", {"coppa": False, "auto_cache": True, "smart_banners": False}),
        ("PATCH", f"/apps/{android_app_key}", {"coppa": False, "auto_cache": True}),
        ("POST", f"/apps/{android_app_key}/placements", {"name": "default", "ad_type": "interstitial"}),
        ("PUT", f"/apps/{android_app_key}/placements/default", {"frequency_cap": 0, "interval": 0}),
        ("PUT", f"/apps/{ios_app_key}", {"coppa": False, "auto_cache": True}),
        ("POST", f"/apps/{ios_app_key}/placements", {"name": "default", "ad_type": "interstitial"}),
        ("DELETE", f"/apps/{android_app_key}/placements/test_placement", None)
    ]

    tasks = []
    for base in base_urls:
        for method, ep, payload in endpoints_to_test:
            for idx, h in enumerate(headers_options):
                tasks.append((base, method, ep, payload, h, api_key, user_id, idx))

    print(f"Queued {len(tasks)} API call combinations. Executing concurrently...")

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(test_single_endpoint, t) for t in tasks]
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    audit_results["management_api_attempts"] = results
    print(f"Completed testing {len(results)} API combinations.")

    # Filter non-404/405/401/403 successes
    successes = [r for r in results if r.get("status_code") not in [404, 405, 401, 403, None]]
    print(f"\nNon-standard response status count: {len(successes)}")
    for s in successes:
        print(f"★ [{s.get('method')}] {s.get('url')} -> Status {s.get('status_code')} | Resp: {s.get('response_preview')}")

    # Write output to docs/appodeal_api_audit_results.json
    out_dir = os.path.join(PROJECT_DIR, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "appodeal_api_audit_results.json")
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Detailed audit results saved to: {out_file}")
    print("==========================================================")

if __name__ == "__main__":
    main()
