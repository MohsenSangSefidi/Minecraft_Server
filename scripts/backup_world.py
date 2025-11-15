#!/usr/bin/env python3
import os
import sys
import shutil
import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def create_backup():
    """Create a backup of the Minecraft world"""
    world_dir = Path("server/world")
    backups_dir = Path("backups")

    if not world_dir.exists():
        print("❌ World directory not found")
        return False

    backups_dir.mkdir(exist_ok=True)

    # Create backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"world_backup_{timestamp}"
    backup_path = backups_dir / backup_name

    try:
        print(f"💾 Creating backup: {backup_name}")
        shutil.copytree(world_dir, backup_path)
        print(f"✅ Backup created successfully: {backup_name}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def list_backups():
    """List all available backups"""
    backups_dir = Path("backups")

    if not backups_dir.exists():
        print("ℹ️  No backups found")
        return

    backups = [d for d in backups_dir.iterdir() if d.is_dir()]

    if not backups:
        print("ℹ️  No backups found")
        return

    print(f"📋 Available backups ({len(backups)}):")
    for backup in sorted(backups):
        print(f"   - {backup.name}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_backups()
    else:
        create_backup()