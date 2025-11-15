#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to Python path to find src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from src.forge_manager import ForgeManager
    from src.mod_manager import ModManager

    print("✅ Successfully imported modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📁 Current directory:", os.getcwd())
    print("📁 Python path:", sys.path)
    sys.exit(1)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def main():
    print("🚀 Setting up Forge Minecraft Server...")
    setup_logging()

    # Create necessary directories first
    directories = ['config', 'mods', 'server', 'logs', 'src']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # Check for required config files
    config_files = {
        'server_config.json': {
            "minecraft_version": "1.20.1",
            "forge_version": "47.2.0",
            "memory": {
                "max": "4G",
                "min": "2G"
            },
            "server_properties": {
                "motd": "Forge Server on GitHub Codespaces",
                "max-players": 10,
                "view-distance": 8,
                "online-mode": False,
                "enable-command-block": True
            }
        },
        'gateway_config.json': {
            "dashboard_port": 8080,
            "minecraft_port": 25565
        },
        'mods_config.json': {
            "auto_download": False,
            "mods": {}
        }
    }

    # Create config files if they don't exist
    for config_file, default_config in config_files.items():
        config_path = Path("config") / config_file
        if not config_path.exists():
            import json
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Created config file: {config_file}")

    # Setup Forge server
    print("📥 Setting up Forge server...")
    forge_manager = ForgeManager()

    # Download and install Forge
    if forge_manager.install_forge_server():
        print("✅ Forge server installed successfully")
    else:
        print("❌ Failed to install Forge server")
        return

    # Setup server properties
    forge_manager.setup_server_properties()
    print("✅ Server configuration complete")

    # Setup mods
    mod_manager = ModManager()
    if mod_manager.config.get("auto_download", False):
        mod_manager.download_all_mods()
        print("✅ Mods downloaded")
    else:
        print("ℹ️  Auto-download disabled. Add mods to 'mods/' directory.")

    print("\n🎯 Forge setup completed!")
    print("\n📝 Next steps:")
    print("   1. Add mod .jar files to the 'mods/' directory (optional)")
    print("   2. Run: python main.py")
    print("   3. Connect to: localhost:25565")
    print("   4. Access web dashboard: http://localhost:8080")
    print("\n⚠️  Note: First startup may take several minutes as Forge sets up")


if __name__ == "__main__":
    main()
