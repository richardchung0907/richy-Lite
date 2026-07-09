#!/usr/bin/env python3
"""
BERRY → RICHY — Project-Wide Rename Script
============================================
Safely renames every occurrence of "Berry"/"BERRY"/"berry" to
"Richy"/"RICHY"/"richy" across ALL editable project files:

  • File contents (case-aware, 3-pass replacement)
  • File & directory names
  • Class names, imports, string literals, comments, docs
  • Package identifiers (com.berrylite → com.richylite)
  • Asset paths, log filenames, User-Agent strings

Dry-run mode (default):  python rename_berry_to_richy.py
Live mode:               python rename_berry_to_richy.py --live

The script:
  - Skips binary files, .git/, __pycache__/, build_logs/, error_logs/
  - Prints every changed line with before/after diff
  - Leaves a detailed change log at build_logs/rename_YYYYMMDD_HHMMSS.log
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Configuration ─────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Files/dirs to skip entirely
SKIP_DIRS = {
    ".git",
    "__pycache__",
    "build_logs",
    "error_logs",
    "build",
    ".dart_tool",
    ".codewhale",
    "android/.gradle",
    "android/app/build",
    "ios/Pods",
    "ios/.symlinks",
    "ios/Flutter",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns",
    ".webp", ".bmp", ".svg",  # images (but SVG could be edited)
    ".ttf", ".otf", ".woff", ".woff2",  # fonts
    ".mp3", ".mp4", ".wav", ".aac",  # audio/video
    ".zip", ".tar", ".gz", ".7z", ".rar",  # archives
    ".pyc", ".pyo",  # compiled python
    ".lock",  # lock files (but pubspec.lock is skipped anyway)
    ".keystore", ".jks", ".p12",  # certs
}

EDITABLE_EXTENSIONS = {
    ".dart", ".py", ".yaml", ".yml", ".json", ".xml", ".plist",
    ".md", ".txt", ".gradle", ".properties", ".cfg", ".ini",
    ".html", ".css", ".js", ".ts", ".sh", ".bat", ".ps1",
    ".gitignore",  # dotfiles
    ".swift", ".kt", ".java", ".m", ".h", ".mm",
}

# ── Logging ────────────────────────────────────────────────────────
LOG_DIR = os.path.join(PROJECT_DIR, "build_logs")
LOG_FILE = os.path.join(
    LOG_DIR,
    f"rename_{datetime.now():%Y%m%d_%H%M%S}.log",
)
CHANGES: list[str] = []  # human-readable change log


def log(msg: str):
    """Print and log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def record_change(rel_path: str, before: str, after: str, line_num: int = 0):
    """Record a single change for the summary."""
    entry = f"  {rel_path}:{line_num}  \"{before}\" → \"{after}\""
    CHANGES.append(entry)
    log(entry)


# ── File Discovery ─────────────────────────────────────────────────


def should_skip(path: str) -> bool:
    """Check if a file or directory should be skipped."""
    rel = os.path.relpath(path, PROJECT_DIR).replace("\\", "/")

    # Skip directories
    parts = rel.split("/")
    for i in range(len(parts)):
        prefix = "/".join(parts[: i + 1])
        if prefix in SKIP_DIRS:
            return True

    # Skip by extension
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTENSIONS:
        return True

    # Also skip the rename script itself
    if os.path.basename(path) == "rename_berry_to_richy.py":
        return True

    return False


def iter_editable_files(root: str):
    """Yield (full_path, relative_path) for all editable files."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Filter out skipped dirs in-place
        dirnames[:] = [
            d for d in dirnames
            if not should_skip(os.path.join(dirpath, d))
        ]

        for fname in filenames:
            full = os.path.join(dirpath, fname)
            if should_skip(full):
                continue
            rel = os.path.relpath(full, root)
            yield full, rel


# ── Content Replacement ────────────────────────────────────────────


def replace_in_content(content: str, file_path: str) -> tuple[str, int]:
    """Apply all Berry→Richy replacements to content.

    Performs 3 case-aware passes and returns (new_content, change_count).
    Each matched occurrence is logged.
    """
    rel = os.path.relpath(file_path, PROJECT_DIR)
    changes = 0

    # ── Pass 1: BERRY → RICHY (ALL-CAPS, literal substring) ───
    # Use literal replace (not \b) to catch BERRY inside
    # compound forms like BERRY-Lite-Setup, BERRY_LITE, etc.
    matches_upper = [m for m in re.finditer(r"BERRY", content)]
    for m in reversed(matches_upper):
        line_num = content[: m.start()].count("\n") + 1
        record_change(rel, "BERRY", "RICHY", line_num)
    new_content = content.replace("BERRY", "RICHY")
    if new_content != content:
        changes += len(matches_upper)
        content = new_content

    # ── Pass 2: Berry → Richy (Title Case, literal substring) ─
    matches_title = [m for m in re.finditer(r"Berry", content)]
    for m in reversed(matches_title):
        line_num = content[: m.start()].count("\n") + 1
        record_change(rel, "Berry", "Richy", line_num)
    new_content = content.replace("Berry", "Richy")
    if new_content != content:
        changes += len(matches_title)
        content = new_content

    # ── Pass 3: berry → richy (lowercase, literal substring) ──
    matches_lower = [m for m in re.finditer(r"berry", content)]
    for m in reversed(matches_lower):
        line_num = content[: m.start()].count("\n") + 1
        record_change(rel, "berry", "richy", line_num)
    new_content = content.replace("berry", "richy")
    if new_content != content:
        changes += len(matches_lower)
        content = new_content

    return content, changes


# ── Filename Renaming ──────────────────────────────────────────────


def rename_files_and_dirs(root: str, live: bool = False) -> int:
    """Rename files and directories containing 'berry' (any case).

    Process bottom-up so files are renamed before their parent dirs.
    Returns count of renamed items.
    """
    log("── Phase 2: Renaming files & directories ──")
    renames = 0

    # Collect all items bottom-up
    items_to_rename: list[tuple[str, str, bool]] = []  # (full_path, new_name, is_dir)
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Skip excluded
        dirnames[:] = [d for d in dirnames if not should_skip(os.path.join(dirpath, d))]

        for name in filenames + dirnames:
            full = os.path.join(dirpath, name)
            if should_skip(full):
                continue
            if "berry" in name.lower():
                is_dir = os.path.isdir(full)
                new_name = name.replace("BERRY", "RICHY").replace("Berry", "Richy").replace("berry", "richy")
                if new_name != name:
                    items_to_rename.append((full, new_name, is_dir))

    # Rename bottom-up (sort by depth descending)
    items_to_rename.sort(key=lambda x: x[0].count(os.sep), reverse=True)

    for old_path, new_name, is_dir in items_to_rename:
        parent = os.path.dirname(old_path)
        new_path = os.path.join(parent, new_name)
        rel_old = os.path.relpath(old_path, PROJECT_DIR)
        rel_new = os.path.relpath(new_path, PROJECT_DIR)
        log(f"  {rel_old} → {rel_new}")
        if live:
            try:
                os.rename(old_path, new_path)
                renames += 1
            except OSError as e:
                log(f"    ✗ Failed: {e}")

    return renames


# ── Main ──────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="BERRY → RICHY project-wide rename"
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Actually perform the rename (default is dry-run)",
    )
    parser.add_argument(
        "--no-rename-files", action="store_true",
        help="Only replace content, don't rename files/dirs",
    )
    args = parser.parse_args()

    mode = "LIVE" if args.live else "DRY-RUN"
    log("=" * 60)
    log(f"  BERRY -> RICHY  Project Rename  [{mode}]")
    log(f"  Project: {PROJECT_DIR}")
    log(f"  Log:     {LOG_FILE}")
    log("=" * 60)

    # ── Phase 1: Content Replacement ──────────────────────────
    log("\n▶ Phase 1: Content Replacement")
    total_files = 0
    changed_files = 0
    total_changes = 0

    for full_path, rel_path in iter_editable_files(PROJECT_DIR):
        total_files += 1
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                original = f.read()
        except Exception as e:
            log(f"  ⚠ Cannot read {rel_path}: {e}")
            continue

        new_content, changes = replace_in_content(original, full_path)
        if changes > 0:
            changed_files += 1
            total_changes += changes
            log(f"  ✓ {rel_path} ({changes} changes)")

            if args.live:
                try:
                    with open(full_path, "w", encoding="utf-8", newline="") as f:
                        f.write(new_content)
                except Exception as e:
                    log(f"    ✗ Failed to write {rel_path}: {e}")

    # ── Phase 2: Filename Renaming ────────────────────────────
    renames = 0
    if not args.no_rename_files:
        renames = rename_files_and_dirs(PROJECT_DIR, live=args.live)

    # ── Summary ───────────────────────────────────────────────
    log("\n" + "=" * 60)
    log(f"  SUMMARY  [{mode}]")
    log(f"  Files scanned:      {total_files}")
    log(f"  Files changed:      {changed_files}")
    log(f"  Content changes:    {total_changes}")
    log(f"  File/dir renames:   {renames}")
    log("=" * 60)

    if not args.live:
        log("\n  ℹ This was a DRY-RUN. No files were modified.")
        log("    Run with --live to apply changes.")
        log("")
        log("    IMPORTANT: Commit your work (git commit) before")
        log("    running --live so you can revert if needed.")
    else:
        log(f"\n  ✓ All changes applied!")
        log(f"    Full change log: {LOG_FILE}")

    if total_changes > 0 and args.live:
        log("\n── Changed files ──")
        for c in CHANGES:
            log(c)


if __name__ == "__main__":
    main()
