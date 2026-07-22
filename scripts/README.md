# RICHY Lite Development & Automation Scripts

Welcome, developer or AI agent! This directory contains the complete automation and toolchain suite for the RICHY Lite project. 

> [!IMPORTANT]
> **BEFORE WRITING ANY NEW SCRIPTS OR REINVENTING THE WHEEL:**
> You must review the existing tool list below. If an existing script performs a similar function, you must reuse, refine, or import it rather than creating a new one.

---

## 📦 Available Scripts Index

### 1. Local Development & Emulation
- **[run_app.py](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/run_app.py)**
  - *Purpose*: Boots the Android emulator, resolves stale ADB ports or process conflicts, and launches `flutter run` with Hot Reload.
  - *Usage*: `python scripts/run_app.py` or with `--only-build` / `--only-run`.

- **[deploy_apk.py](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/deploy_apk.py)**
  - *Purpose*: Decoupled installation and launch of release AOT APKs onto local Android emulators (`emulator-5554`) using **WMI (`Win32_Process`)**. This ensures the emulator window is visible on Windows interactive desktops and survives tool termination. Also handles signature override uninstalls.
  - *Usage*: `python scripts/deploy_apk.py`

### 2. Remote Build & Actions Automation
- **[github_build_handler.py](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/github_build_handler.py)**
  - *Purpose*: Automates pushing the active branch and generating an isolated release tag to trigger GitHub Actions compilation. Polls remote status via the GitHub API every 2 minutes, downloads the compiled release artifact, extracts `app-release.apk` to `build_artifacts/`, and cleans up zips.
  - *Usage*: `python scripts/github_build_handler.py`

- **[setup_github_secrets.py](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/setup_github_secrets.py)**
  - *Purpose*: Resolves Libsodium/pynacl encryption to package, encrypt, and upload signing keystores, key properties, and API tokens to GitHub Actions secrets.
  - *Usage*: `python scripts/setup_github_secrets.py`

### 3. Pipeline Build Orchestration
- **[build_android.py](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/build_android.py)**
  - *Purpose*: Main Android build pipeline tool. Checks environments, runs `flutter pub get` and `flutter analyze`, and builds debug or release APKs or App Bundles.
  - *Usage*: `python scripts/build_android.py --release`

- **[build_ios.py](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/build_ios.py)**
  - *Purpose*: iOS build pipeline helper. Handles environment checks, cocoapod recovery, and guides EAS cloud compiling setups on non-macOS systems.
  - *Usage*: `python scripts/build_ios.py`

- **[setup_and_build.py](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/setup_and_build.py)**
  - *Purpose*: Full bootstrap utility. Downloads, installs and configures Flutter SDK, JDK 17, and Android SDK from scratch on a clean Windows machine before running compilation pipelines.
  - *Usage*: `python scripts/setup_and_build.py`

---

## 🛠️ Script Design Standards

If you must modify or add a script to this directory, you **must** adhere to the following guidelines:
1. **Decoupled Execution Path**: Because these scripts reside in `scripts/`, they must run from the project root. Always include this bootstrap code at the top of any python script to change the current working directory to the project root:
   ```python
   import os
   import sys
   SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
   PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
   os.chdir(PROJECT_DIR)
   if PROJECT_DIR not in sys.path:
       sys.path.insert(0, PROJECT_DIR)
   if SCRIPT_DIR not in sys.path:
       sys.path.insert(0, SCRIPT_DIR)
   ```
2. **Zero Sensitive Data Leakage**: Never commit keys, private tokens, or keystore passwords directly to scripts. Always load them dynamically from `keys.txt` (which is git-ignored) or system environment variables.
