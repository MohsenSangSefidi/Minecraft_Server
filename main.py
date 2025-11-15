#!/usr/bin/env python3
import os
import time
import signal
import sys
import threading
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from forge_manager import ForgeManager
from gateway_manager import GatewayManager
from mod_manager import ModManager


class ForgeServerApp:
    def __init__(self):
        self.setup_logging()
        self.forge_manager = ForgeManager()
        self.gateway_manager = GatewayManager()
        self.mod_manager = ModManager()
        self.running = False

    def setup_logging(self):
        """Setup comprehensive logging"""
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/app.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def start_gateway(self):
        """Start the gateway in a separate thread"""

        def run_gateway():
            try:
                from gateway_server import main as gateway_main
                gateway_main()
            except Exception as e:
                self.logger.error(f"Gateway error: {e}")

        gateway_thread = threading.Thread(target=run_gateway, daemon=True)
        gateway_thread.start()
        self.logger.info("Gateway server started in separate thread")

    def start(self):
        """Start the complete Forge server system"""
        self.logger.info("🚀 Starting Forge Minecraft Server with Custom Gateway...")

        # Create necessary directories
        self.create_directories()

        # Download mods if configured
        if self.mod_manager.config["auto_download"]:
            self.mod_manager.download_all_mods()

        # Start Forge server
        self.logger.info("Starting Forge server...")
        if not self.forge_manager.start_server():
            self.logger.error("❌ Failed to start Forge server")
            return False

        # Wait for Forge server to initialize (mods take time to load)
        self.logger.info("⏳ Waiting for Forge server to initialize (this may take a few minutes)...")
        time.sleep(30)

        # Start gateway system
        self.logger.info("Starting gateway system...")
        self.start_gateway()

        # Display connection information
        self.display_connection_info()

        return True

    def create_directories(self):
        """Create all necessary directories"""
        directories = [
            "server",
            "server/mods",
            "server/config",
            "server/logs",
            "server/crash-reports",
            "mods",
            "config",
            "logs",
            "backups",
            "gateway",
            "gateway/connections",
            "gateway/logs",
            "static/css",
            "static/js",
            "templates"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def display_connection_info(self):
        """Display connection information to the user"""
        self.logger.info("=" * 70)
        self.logger.info("🎮 FORGE SERVER WITH CUSTOM GATEWAY IS READY! 🎮")
        self.logger.info("=" * 70)
        self.logger.info(f"🔧 Minecraft Version: {self.forge_manager.config['minecraft_version']}")
        self.logger.info(f"⚙️  Forge Version: {self.forge_manager.config['forge_version']}")
        self.logger.info(f"📦 Mods Installed: {self.forge_manager.get_server_info()['mods_count']}")
        self.logger.info("")
        self.logger.info("🌐 CONNECTION METHODS:")
        self.logger.info(f"   Direct Connect: localhost:25565")
        self.logger.info(f"   Web Dashboard: http://localhost:{self.gateway_manager.config['dashboard_port']}")
        self.logger.info(f"   Gateway API: http://localhost:{self.gateway_manager.config['gateway_port']}")
        self.logger.info("")
        self.logger.info("📝 INSTRUCTIONS:")
        self.logger.info("   1. Use the web dashboard to create connection codes")
        self.logger.info("   2. Share connection codes with friends")
        self.logger.info("   3. Friends can connect using the provided addresses")
        self.logger.info("")
        self.logger.info("⚠️  IMPORTANT: In GitHub Codespaces, ports are automatically forwarded")
        self.logger.info("   Check the 'Ports' tab in VS Code for public URLs")
        self.logger.info("=" * 70)

    def stop(self):
        """Stop everything gracefully"""
        self.logger.info("🛑 Shutting down Forge server system...")
        self.forge_manager.stop_server()
        self.running = False
        self.logger.info("✅ Server system stopped")

    def run(self):
        """Main application loop"""
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            if self.start():
                self.logger.info("✅ Server system is running. Press Ctrl+C to stop.")

                # Main monitoring loop
                while self.running:
                    time.sleep(1)

                    # Check if Forge server is still running
                    if not self.forge_manager.is_running():
                        self.logger.warning("⚠️ Forge server stopped unexpectedly")
                        break

        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            self.stop()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)


if __name__ == "__main__":
    # Check if we're in a Codespaces environment
    if os.getenv('CODESPACES'):
        print("🌐 Detected GitHub Codespaces environment")
        print("📡 Ports will be automatically forwarded")

    app = ForgeServerApp()
    app.run()