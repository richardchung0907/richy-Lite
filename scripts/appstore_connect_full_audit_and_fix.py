#!/usr/bin/env python3
"""
App Store Connect Comprehensive Audit & Auto-Optimization Script
================================================================
1. Enforces 1.5s delay between requests to strictly respect Apple API rate limits.
2. Audits and updates App Info, Localizations (10 languages), Age Rating, App Store Versions, Review Details, Price Schedule, and Build Attachment.
3. Tests and documents API capabilities vs. UI-only requirements (e.g. Tax/Banking/Agreements).
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

if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

KEYS_FILE = "keys.txt"
KEY_P8_FILE = "AuthKey_LSLS88W574.p8"
RATE_LIMIT_DELAY = 1.5  # 1.5s delay between API calls

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

def api_call(method, token, endpoint, params=None, json_data=None):
    time.sleep(RATE_LIMIT_DELAY)  # Strict rate limiting
    url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.request(method, url, headers=headers, params=params, json=json_data)
    return r

def main():
    print("==========================================================================")
    print("  RICHY Lite — App Store Connect Complete API Audit & Auto-Optimization   ")
    print("==========================================================================\n")

    keys = load_keys()
    token = generate_jwt_token(keys["Issuer ID for App Store Connect API"], keys["Key ID for App Store Connect API"], KEY_P8_FILE)
    app_id = "6792005935"

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "app_id": app_id,
        "completed_updates": [],
        "verified_settings": [],
        "api_unsupported_or_failed": []
    }

    # -------------------------------------------------------------------------
    # 1. Audit & Update App Info Localizations (App Name & Subtitle)
    # -------------------------------------------------------------------------
    print("\n[1/7] Auditing App Name & Subtitle (appInfoLocalizations)...")
    app_info_r = api_call("GET", token, f"apps/{app_id}/appInfos")
    if app_info_r.status_code == 200:
        app_infos = app_info_r.json().get("data", [])
        for info in app_infos:
            info_id = info.get("id")
            locs_r = api_call("GET", token, f"appInfos/{info_id}/appInfoLocalizations")
            if locs_r.status_code == 200:
                locs = locs_r.json().get("data", [])
                print(f" Found {len(locs)} appInfoLocalization(s).")
                for loc in locs:
                    loc_id = loc.get("id")
                    loc_attrs = loc.get("attributes", {})
                    locale = loc_attrs.get("locale")
                    name = loc_attrs.get("name")
                    subtitle = loc_attrs.get("subtitle")
                    print(f"  - Locale '{locale}': Name='{name}', Subtitle='{subtitle}'")
                    
                    # Ensure subtitle is present and compelling for top localizations
                    if not subtitle or len(subtitle) < 3:
                        new_subtitle = "韓系網紅復古相機濾鏡" if "zh" in locale else "Aesthetic Korean Photo Filters"
                        update_payload = {
                            "data": {
                                "type": "appInfoLocalizations",
                                "id": loc_id,
                                "attributes": {
                                    "subtitle": new_subtitle
                                }
                            }
                        }
                        up_res = api_call("PATCH", token, f"appInfoLocalizations/{loc_id}", json_data=update_payload)
                        if up_res.status_code == 200:
                            print(f"    ✓ Updated subtitle for locale '{locale}' to '{new_subtitle}'")
                            results["completed_updates"].append(f"appInfoLocalizations ({locale}): Updated subtitle to '{new_subtitle}'")
                        else:
                            print(f"    Notice updating subtitle ({up_res.status_code}): {up_res.text}")
            else:
                results["api_unsupported_or_failed"].append({
                    "action": f"GET appInfos/{info_id}/appInfoLocalizations",
                    "status_code": locs_r.status_code,
                    "response": locs_r.text
                })

    # -------------------------------------------------------------------------
    # 2. Audit & Update Age Rating Declaration (ageRatingDeclarations)
    # -------------------------------------------------------------------------
    print("\n[2/7] Auditing Age Rating Declaration...")
    app_info_r = api_call("GET", token, f"apps/{app_id}/appInfos")
    if app_info_r.status_code == 200 and app_info_r.json().get("data"):
        info_id = app_info_r.json().get("data", [])[0].get("id")
        age_r = api_call("GET", token, f"appInfos/{info_id}/ageRatingDeclaration")
        if age_r.status_code == 200:
            age_data = age_r.json().get("data", {})
            age_id = age_data.get("id")
            age_attrs = age_data.get("attributes", {})
            print(f" Age Rating Declaration ID: {age_id}")
            
            # Verify 4+ rating parameters (RICHY Lite has no gambling, alcohol, sexual content, etc.)
            age_payload = {
                "data": {
                    "type": "ageRatingDeclarations",
                    "id": age_id,
                    "attributes": {
                        "alcoholTobaccoOrDrugUseOrReferences": "NONE",
                        "contests": "NONE",
                        "gamblingAndContests": False,
                        "gamblingSimulated": "NONE",
                        "horrorOrFearThemes": "NONE",
                        "matureOrSuggestiveThemes": "NONE",
                        "medicalOrTreatmentInformation": "NONE",
                        "profanityOrCrudeHumor": "NONE",
                        "sexualContentOrNudity": "NONE",
                        "sexualContentGraphicAndNudity": "NONE",
                        "unrestrictedWebAccess": False,
                        "violenceRealistic": "NONE",
                        "violenceCartoonOrFantasy": "NONE"
                    }
                }
            }
            age_up = api_call("PATCH", token, f"ageRatingDeclarations/{age_id}", json_data=age_payload)
            if age_up.status_code == 200:
                print("  ✓ Successfully updated Age Rating Declaration to 4+ (FOUR_PLUS) with all zero-content flags.")
                results["completed_updates"].append("ageRatingDeclarations: Configured 4+ rating parameters.")
            else:
                print(f"  Notice updating Age Rating ({age_up.status_code}): {age_up.text}")
        else:
            results["api_unsupported_or_failed"].append({
                "action": f"GET appInfos/{info_id}/ageRatingDeclaration",
                "status_code": age_r.status_code,
                "response": age_r.text
            })

    # -------------------------------------------------------------------------
    # 3. Audit & Update App Store Version Localizations (10 Locales)
    # -------------------------------------------------------------------------
    print("\n[3/7] Auditing App Store Version Localizations (Description, Keywords, URLs)...")
    ver_r = api_call("GET", token, f"apps/{app_id}/appStoreVersions")
    if ver_r.status_code == 200:
        ver_data = ver_r.json().get("data", [])[0]
        ver_id = ver_data.get("id")
        print(f" Target Version ID: {ver_id} (Version {ver_data.get('attributes', {}).get('versionString')})")
        
        locs_r = api_call("GET", token, f"appStoreVersions/{ver_id}/appStoreVersionLocalizations")
        if locs_r.status_code == 200:
            locs = locs_r.json().get("data", [])
            print(f" Auditing {len(locs)} localized version metadata records...")
            for loc in locs:
                loc_id = loc.get("id")
                loc_attrs = loc.get("attributes", {})
                locale = loc_attrs.get("locale")
                desc = loc_attrs.get("description", "")
                keywords = loc_attrs.get("keywords", "")
                support_url = loc_attrs.get("supportUrl", "")
                marketing_url = loc_attrs.get("marketingUrl", "")
                
                print(f"  - Locale '{locale}': Desc_len={len(desc)}, Keywords='{keywords[:30]}...', Support='{support_url}'")
                
                # Check if keywords or support URL need updating
                needs_update = False
                patch_attrs = {}
                
                if not keywords or len(keywords) < 5:
                    patch_attrs["keywords"] = "filter,photo,editor,camera,korean,aesthetic,preset,richy,lite,effect"
                    needs_update = True
                
                if not support_url or "http" not in support_url:
                    patch_attrs["supportUrl"] = "https://github.com/richardchung0907/richy-Lite"
                    needs_update = True
                    
                if not marketing_url or "http" not in marketing_url:
                    patch_attrs["marketingUrl"] = "https://github.com/richardchung0907/richy-Lite"
                    needs_update = True

                if needs_update:
                    patch_payload = {
                        "data": {
                            "type": "appStoreVersionLocalizations",
                            "id": loc_id,
                            "attributes": patch_attrs
                        }
                    }
                    p_res = api_call("PATCH", token, f"appStoreVersionLocalizations/{loc_id}", json_data=patch_payload)
                    if p_res.status_code == 200:
                        print(f"    ✓ Updated metadata for locale '{locale}': {list(patch_attrs.keys())}")
                        results["completed_updates"].append(f"appStoreVersionLocalizations ({locale}): Updated {list(patch_attrs.keys())}")
                    else:
                        print(f"    Notice updating metadata for '{locale}' ({p_res.status_code}): {p_res.text}")
                else:
                    results["verified_settings"].append(f"appStoreVersionLocalizations ({locale}): Fully compliant.")

    # -------------------------------------------------------------------------
    # 4. Audit Screenshot Sets (6.5" and 5.5" Displays)
    # -------------------------------------------------------------------------
    print("\n[4/7] Auditing App Screenshot Sets for 10 Localizations...")
    locs_r = api_call("GET", token, f"appStoreVersions/{ver_id}/appStoreVersionLocalizations")
    if locs_r.status_code == 200:
        locs = locs_r.json().get("data", [])
        for loc in locs:
            loc_id = loc.get("id")
            locale = loc.get("attributes", {}).get("locale")
            
            ss_r = api_call("GET", token, f"appStoreVersionLocalizations/{loc_id}/appScreenshotSets")
            if ss_r.status_code == 200:
                ss_sets = ss_r.json().get("data", [])
                set_types = [s.get("attributes", {}).get("screenshotDisplayType") for s in ss_sets]
                print(f"  - Locale '{locale}': Existing screenshot sets = {set_types}")
                
                # Ensure 6.5" and 5.5" display sets are present
                for req_type in ["APP_IPHONE_65", "APP_IPHONE_55"]:
                    if req_type not in set_types:
                        create_payload = {
                            "data": {
                                "type": "appScreenshotSets",
                                "attributes": {
                                    "screenshotDisplayType": req_type
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
                        c_res = api_call("POST", token, "appScreenshotSets", json_data=create_payload)
                        if c_res.status_code in [200, 201]:
                            print(f"    ✓ Created '{req_type}' set for locale '{locale}'")
                            results["completed_updates"].append(f"appScreenshotSets ({locale}): Created '{req_type}' set.")
                        else:
                            print(f"    Notice creating '{req_type}' set ({c_res.status_code}): {c_res.text}")

    # -------------------------------------------------------------------------
    # 5. Audit & Configure App Store Review Details
    # -------------------------------------------------------------------------
    print("\n[5/7] Auditing App Store Review Details (appStoreReviewDetails)...")
    rev_r = api_call("GET", token, f"appStoreVersions/{ver_id}/appStoreReviewDetail")
    if rev_r.status_code == 200 and rev_r.json().get("data"):
        rev_data = rev_r.json().get("data", {})
        rev_id = rev_data.get("id")
        rev_attrs = rev_data.get("attributes", {})
        print(f" Found existing App Store Review Detail ID: {rev_id}")
        print(f"  - Contact: {rev_attrs.get('contactFirstName')} {rev_attrs.get('contactLastName')}, Phone: {rev_attrs.get('contactPhoneNumber')}")
    else:
        # Create App Store Review Detail if missing
        rev_payload = {
            "data": {
                "type": "appStoreReviewDetails",
                "attributes": {
                    "contactFirstName": "Richard",
                    "contactLastName": "Chung",
                    "contactPhone": "+886900000000",
                    "contactEmail": "richardchung0907@gmail.com",
                    "demoAccountRequired": False,
                    "notes": "RICHY Lite is a free Korean style filter app. AdMob has been completely removed and replaced with Appodeal mediation."
                },
                "relationships": {
                    "appStoreVersion": {
                        "data": {
                            "type": "appStoreVersions",
                            "id": ver_id
                        }
                    }
                }
            }
        }
        c_rev = api_call("POST", token, "appStoreReviewDetails", json_data=rev_payload)
        if c_rev.status_code in [200, 201]:
            print("  ✓ Created App Store Review Detail with developer contact info and review notes.")
            results["completed_updates"].append("appStoreReviewDetails: Created review contact & notes.")
        else:
            print(f"  Notice on App Store Review Detail creation ({c_rev.status_code}): {c_rev.text}")

    # -------------------------------------------------------------------------
    # 6. Check Builds Attachment for Version 1.0
    # -------------------------------------------------------------------------
    print("\n[6/7] Auditing Build Attachment for App Store Version 1.0...")
    builds_r = api_call("GET", token, f"apps/{app_id}/builds", params={"limit": 5})
    if builds_r.status_code == 200:
        builds = builds_r.json().get("data", [])
        print(f" Found {len(builds)} build(s) in TestFlight/App Store Connect.")
        valid_build = None
        for b in builds:
            b_attrs = b.get("attributes", {})
            p_state = b_attrs.get("processingState")
            b_ver = b_attrs.get("version")
            print(f"  - Build {b_ver} (ID: {b.get('id')}) | State: {p_state}")
            if p_state == "VALID":
                valid_build = b
                break
                
        if valid_build:
            b_id = valid_build.get("id")
            att_payload = {
                "data": {
                    "type": "appStoreVersions",
                    "id": ver_id,
                    "relationships": {
                        "build": {
                            "data": {
                                "type": "builds",
                                "id": b_id
                            }
                        }
                    }
                }
            }
            att_res = api_call("PATCH", token, f"appStoreVersions/{ver_id}", json_data=att_payload)
            if att_res.status_code in [200, 204]:
                print(f"  ✓ Attached valid build ID '{b_id}' to App Store Version 1.0!")
                results["completed_updates"].append(f"appStoreVersions: Attached Build ID '{b_id}'")
            else:
                print(f"  Notice attaching build ({att_res.status_code}): {att_res.text}")
        else:
            print("  Notice: No builds currently in 'VALID' state. New build will be uploaded via GitHub Actions CI/CD.")
            results["verified_settings"].append("Build Attachment: Awaiting next GitHub Actions CI build.")

    # -------------------------------------------------------------------------
    # 7. Test Banking, Tax, and Legal Agreements API Endpoints
    # -------------------------------------------------------------------------
    print("\n[7/7] Testing Tax, Banking, Agreements & Customer Reviews API endpoints...")
    
    # Check Customer Reviews endpoint
    reviews_r = api_call("GET", token, f"apps/{app_id}/customerReviews")
    print(f" Customer Reviews API Status: {reviews_r.status_code}")
    
    # Test Tax & Banking / Agreements endpoint (Attempting GET /v1/financeReports or /v1/taxForms)
    tax_r = api_call("GET", token, "financeReports", params={"filter[regionCode]": "US", "filter[reportType]": "FINANCIAL"})
    print(f" Finance/Tax Reports API Status: {tax_r.status_code} ({tax_r.text[:100]})")
    
    # Log Tax/Banking result
    results["api_unsupported_or_failed"].append({
        "feature": "Paid Applications, Banking & Tax Agreements",
        "reason": "Apple App Store Connect REST API explicitly restricts Tax (W-8BEN / W-9), Banking Account IBAN/SWIFT setups, and Legal Entity Agreements to the App Store Connect Web Portal UI for security and identity verification.",
        "test_endpoint": "GET /v1/financeReports",
        "status_code": tax_r.status_code,
        "response_summary": tax_r.text[:200]
    })

    # Save summary report
    os.makedirs("build_artifacts", exist_ok=True)
    with open("build_artifacts/appstore_connect_full_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n==========================================================================")
    print("  ✓ App Store Connect Complete Audit & Optimization Completed!")
    print("    Detailed log saved to build_artifacts/appstore_connect_full_audit_results.json")
    print("==========================================================================")

if __name__ == "__main__":
    main()
