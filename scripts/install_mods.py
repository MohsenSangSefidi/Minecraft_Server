#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.mod_manager import ModManager


def main():
    print("📦 Installing mods...")

    mods_manager = ModManager()

    # Create mods directory if it doesn't exist
    Path("mods").mkdir(exist_ok=True)

    # Download mods if auto-download is enabled
    if mods_manager.config["auto_download"]:
        print("🔍 Downloading configured mods...")
        mods_manager.download_all_mods()
    else:
        print("ℹ️  Auto-download is disabled. Place mod .jar files in the 'mods/' directory.")

    # List installed mods
    installed_mods = mods_manager.get_installed_mods()
    if installed_mods:
        print(f"✅ Installed mods ({len(installed_mods)}):")
        for mod in installed_mods:
            print(f"   - {mod}")
    else:
        print("ℹ️  No mods installed. Add mod .jar files to the 'mods/' directory.")

    print("\n📝 Next: Run 'python main.py' to start the server with mods")


if __name__ == "__main__":
    main()