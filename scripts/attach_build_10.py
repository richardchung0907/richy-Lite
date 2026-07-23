#!/usr/bin/env python3
import os
import sys
import time
import requests
import jwt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

KEYS_FILE = "keys.txt"
KEY_P8_FILE = "AuthKey_LSLS88W574.p8"

def load_keys():
    keys = {}
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                keys[k.strip()] = v.strip()
    return keys

keys = load_keys()
with open(KEY_P8_FILE, "r", encoding="utf-8") as f:
    private_key = f.read()

headers = {"alg": "ES256", "kid": keys["Key ID for App Store Connect API"], "typ": "JWT"}
payload = {"iss": keys["Issuer ID for App Store Connect API"], "exp": int(time.time()) + 1200, "aud": "appstoreconnect-v1"}
token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

ver_id = "841b3d9a-4111-4808-89cb-3fba95034b0b"
build_10_id = "f477f3a4-4cdf-46f2-99bf-8e6b0cc0ef66" # Build 10

url = f"https://api.appstoreconnect.apple.com/v1/appStoreVersions/{ver_id}/relationships/build"
req_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

payload = {
    "data": {
        "type": "builds",
        "id": build_10_id
    }
}

r = requests.patch(url, headers=req_headers, json=payload)
print("Attach Build Status:", r.status_code)
if r.status_code in [200, 204]:
    print("✓ Successfully attached Build 10 to App Store Version 1.0!")
else:
    print("Response:", r.text)
