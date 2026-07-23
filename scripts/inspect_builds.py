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

app_id = "6792005935"
url = f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/builds?limit=50"
req_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
r = requests.get(url, headers=req_headers)

print("Status Code:", r.status_code)
if r.status_code == 200:
    builds = r.json().get("data", [])
    for b in builds:
        attrs = b.get("attributes", {})
        print(f"Build ID: {b.get('id')} | Version: {attrs.get('version')} | State: {attrs.get('processingState')} | Uploaded: {attrs.get('uploadedDate')}")
else:
    print(r.text)
