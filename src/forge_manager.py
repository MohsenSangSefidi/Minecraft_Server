import subprocess
import psutil
import os
import time
import json
import logging
import requests
import re
from threading import Thread
from pathlib import Path
import shutil


class ForgeManager:
    def __init__(self, config_path="config/server_config.json"):
        self.config_path = config_path
        self.process = None
        self.forge_jar = None
        self.installer_jar = None
        self.load_config()
        self.setup_logging()
        self.ensure_directories()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/forge.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load Forge server configuration"""
        from config_loader import ConfigLoader
        self.config = ConfigLoader.load_server_config()

    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            "server",
            "server/mods",
            "server/config",
            "server/logs",
            "server/crash-reports",
            "mods",
            "config",
            "logs",
            "backups"
        ]

        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

    def get_forge_download_url(self):
        """Get the Forge installer download URL"""
        mc_version = self.config["minecraft_version"]
        forge_version = self.config["forge_version"]

        # Forge version format: minecraft_version-forge_version
        full_version = f"{mc_version}-{forge_version}"

        base_url = "https://maven.minecraftforge.net/net/minecraftforge/forge"
        installer_url = f"{base_url}/{full_version}/forge-{full_version}-installer.jar"

        return installer_url

    def download_forge_installer(self):
        """Download Forge installer"""
        installer_url = self.get_forge_download_url()
        self.installer_jar = f"server/forge-installer.jar"

        self.logger.info(f"Downloading Forge installer from: {installer_url}")

        try:
            response = requests.get(installer_url, stream=True)
            response.raise_for_status()

            with open(self.installer_jar, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info("Forge installer downloaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to download Forge installer: {e}")
            return False

    def install_forge_server(self):
        """Install Forge server using the installer"""
        if not self.installer_jar or not os.path.exists(self.installer_jar):
            if not self.download_forge_installer():
                return False

        self.logger.info("Installing Forge server...")

        try:
            # Run the installer
            install_cmd = [
                "java", "-jar", self.installer_jar,
                "--installServer"
            ]

            result = subprocess.run(
                install_cmd,
                cwd="server",
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info("Forge server installed successfully")

                # Find the forge server jar
                forge_files = list(Path("server").glob("forge-*.jar"))
                if forge_files:
                    self.forge_jar = str(forge_files[0])
                    self.logger.info(f"Found forge jar: {self.forge_jar}")
                    return True
                else:
                    self.logger.error("Could not find forge server jar after installation")
                    return False
            else:
                self.logger.error(f"Forge installation failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error during Forge installation: {e}")
            return False

    def setup_server_properties(self):
        """Create server.properties file optimized for modded server"""
        properties = self.config["server_properties"]

        with open("server/server.properties", "w") as f:
            f.write("# Forge server properties (auto-generated)\n")
            for key, value in properties.items():
                f.write(f"{key}={value}\n")

        # Create eula.txt
        with open("server/eula.txt", "w") as f:
            f.write("eula=true\n")

        self.logger.info("Server properties configured for Forge")

    def copy_mods(self):
        """Copy mods from mods/ directory to server/mods/"""
        mods_source = Path("mods")
        mods_dest = Path("server/mods")

        if mods_source.exists() and any(mods_source.iterdir()):
            self.logger.info("Copying mods to server...")
            for mod_file in mods_source.glob("*.jar"):
                shutil.copy2(mod_file, mods_dest)
                self.logger.info(f"Copied mod: {mod_file.name}")

    def start_server(self):
        """Start the Forge server"""
        if not self.forge_jar or not os.path.exists(self.forge_jar):
            if not self.install_forge_server():
                return False

        self.setup_server_properties()
        self.copy_mods()

        # Build Java command for Forge
        java_cmd = [
            "java",
            f"-Xmx{self.config['memory']['max']}",
            f"-Xms{self.config['memory']['min']}",
        ]

        # Add custom Java arguments
        java_cmd.extend(self.config["java_args"])

        # Add Forge jar
        java_cmd.extend(["-jar", self.forge_jar, "nogui"])

        self.logger.info("Starting Forge server...")
        self.logger.info(f"Java command: {' '.join(java_cmd)}")

        try:
            self.process = subprocess.Popen(
                java_cmd,
                cwd="server",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Start output monitoring in separate thread
            output_thread = Thread(target=self._monitor_output, daemon=True)
            output_thread.start()

            self.logger.info("Forge server started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start Forge server: {e}")
            return False

    def _monitor_output(self):
        """Monitor server output in a separate thread"""
        for line in iter(self.process.stdout.readline, ''):
            if line.strip():
                self.logger.info(f"[Forge] {line.strip()}")

                # Check for server ready message
                if "Done" in line and "For help" in line:
                    self.logger.info("🎯 Forge server is fully loaded and ready!")

    def stop_server(self):
        """Stop the Forge server gracefully"""
        if self.process and self.process.poll() is None:
            self.logger.info("Stopping Forge server...")

            # Send stop command to server
            try:
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()
            except:
                self.logger.warning("Could not send stop command, terminating...")
                self.process.terminate()

            try:
                self.process.wait(timeout=60)
                self.logger.info("Forge server stopped gracefully")
            except subprocess.TimeoutExpired:
                self.logger.warning("Server didn't stop gracefully, forcing...")
                self.process.kill()

    def is_running(self):
        """Check if server is running"""
        return self.process and self.process.poll() is None

    def get_server_info(self):
        """Get server information"""
        return {
            "running": self.is_running(),
            "minecraft_version": self.config["minecraft_version"],
            "forge_version": self.config["forge_version"],
            "memory": self.config["memory"],
            "forge_jar": self.forge_jar,
            "mods_count": len(list(Path("server/mods").glob("*.jar"))) if Path("server/mods").exists() else 0
        }

    def send_rcon_command(self, command):
        """Send command to server via RCON"""
        try:
            rcon_password = self.config["server_properties"]["rcon.password"]
            rcon_port = self.config["server_properties"]["rcon.port"]

            # Using subprocess to call rcon-cli or similar tool
            # This is a simplified version - you might want to use a Python RCON library
            cmd = f"echo '{command}' | nc localhost {rcon_port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            self.logger.error(f"RCON command failed: {e}")
            return None