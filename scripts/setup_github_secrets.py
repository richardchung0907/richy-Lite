#!/usr/bin/env python3
"""
Setup GitHub Action Secrets
===========================
Packages, encrypts, and uploads key properties, keystores, and credentials
from your local environment to GitHub Actions repository secrets using WMI
and Libsodium.
"""

import sys
import subprocess
import os
import base64

# Decouple script location from execution directory by forcing project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_DIR)

# Fix Windows console UTF-8 printing
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Automatically resolve dependencies
try:
    import requests
    import nacl.public
    import nacl.encoding
except ImportError:
    print("Required libraries ('requests' or 'pynacl') are missing. Installing them now...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "pynacl"])
        import requests
        import nacl.public
        import nacl.encoding
        print("Successfully installed 'requests' and 'pynacl'.\n")
    except Exception as e:
        print(f"Failed to install dependencies automatically: {e}")
        print("Please run: pip install requests pynacl")
        sys.exit(1)

# Configuration
REPO_OWNER = "richardchung0907"
REPO_NAME = "richy-Lite"
KEYS_FILE = "keys.txt"
KEY_PROPERTIES_FILE = os.path.join("android", "key.properties")
KEYSTORE_FILE = os.path.join("android", "app", "upload-keystore.jks")

def get_github_token():
    if not os.path.exists(KEYS_FILE):
        print(f"Error: {KEYS_FILE} not found in current directory.")
        sys.exit(1)
    
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Github key:"):
                return line.split("Github key:")[1].strip()
    
    print("Error: Could not find 'Github key' in keys.txt.")
    sys.exit(1)

def get_file_content_base64(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Required signing file not found: {file_path}")
        sys.exit(1)
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def get_text_file_content(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Required signing properties file not found: {file_path}")
        sys.exit(1)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the libsodium SealedBox algorithm as required by GitHub."""
    public_key = nacl.public.PublicKey(public_key_b64.encode("utf-8"), nacl.encoding.Base64Encoder())
    sealed_box = nacl.public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def upload_secret(token, secret_name, secret_value):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Get Public Key
    pub_key_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/public-key"
    r = requests.get(pub_key_url, headers=headers)
    if r.status_code != 200:
        print(f"Failed to fetch public key from GitHub (status: {r.status_code}). Response: {r.text}")
        sys.exit(1)
    
    pub_key_data = r.json()
    key_id = pub_key_data["key_id"]
    public_key_b64 = pub_key_data["key"]
    
    # 2. Encrypt the secret
    encrypted_value = encrypt_secret(public_key_b64, secret_value)
    
    # 3. PUT encrypted secret
    secret_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/{secret_name}"
    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    
    put_r = requests.put(secret_url, headers=headers, json=payload)
    if put_r.status_code in [201, 204]:
        print(f"✓ Secret '{secret_name}' successfully configured on GitHub Actions.")
    else:
        print(f"✗ Failed to upload secret '{secret_name}' (status: {put_r.status_code}). Response: {put_r.text}")

def main():
    print("==========================================================")
    print("  RICHY Lite — GitHub Actions Android Build Setup")
    print("==========================================================\n")
    
    token = get_github_token()
    print("✓ Successfully retrieved GitHub PAT from keys.txt.")
    
    # Read android/key.properties
    key_properties_content = get_text_file_content(KEY_PROPERTIES_FILE)
    print("✓ Loaded android/key.properties content.")
    
    # Read and encode android/app/upload-keystore.jks
    keystore_base64 = get_file_content_base64(KEYSTORE_FILE)
    print("✓ Encoded android/app/upload-keystore.jks to Base64.")
    
    # Upload Secrets to GitHub
    print("\nUploading secrets to richardchung0907/richy-Lite...")
    upload_secret(token, "ANDROID_KEY_PROPERTIES", key_properties_content)
    upload_secret(token, "ANDROID_KEYSTORE_BASE64", keystore_base64)
    
    # Optional AdMob app ID for testing
    upload_secret(token, "ADMOB_ANDROID_APP_ID", "ca-app-pub-3940256099942544~3347511713")
    
    print("\n==========================================================")
    print("  ✓ Setup successful! Your repository is now fully prepared")
    print("    for Android building and signing on GitHub Actions.")
    print("==========================================================")

if __name__ == "__main__":
    main()
