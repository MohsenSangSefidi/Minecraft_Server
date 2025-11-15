#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.forge_manager import ForgeManager
from src.config_loader import ConfigLoader


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

    # Create necessary directories
    directories = ['config', 'mods', 'server', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # Load configuration
    config_loader = ConfigLoader()
    server_config = config_loader.load_server_config()
    gateway_config = config_loader.load_gateway_config()
    mods_config = config_loader.load_mods_config()

    print(f"🔧 Minecraft Version: {server_config['minecraft_version']}")
    print(f"⚙️  Forge Version: {server_config['forge_version']}")
    print(f"💾 Memory: {server_config['memory']['max']}")

    # Setup Forge server
    forge_manager = ForgeManager()

    # Download and install Forge
    print("📥 Downloading and installing Forge server...")
    if forge_manager.install_forge_server():
        print("✅ Forge server installed successfully")
    else:
        print("❌ Failed to install Forge server")
        return

    # Setup server properties
    forge_manager.setup_server_properties()
    print("✅ Server configuration complete")

    # Display next steps
    print("\n🎯 Setup completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Add mod .jar files to the 'mods/' directory")
    print("   2. Run: python main.py")
    print("   3. Access the web dashboard to manage connections")
    print("   4. Share connection codes with friends")
    print("\n⚠️  Note: First startup may take several minutes as Forge sets up mods")


if __name__ == "__main__":
    main()