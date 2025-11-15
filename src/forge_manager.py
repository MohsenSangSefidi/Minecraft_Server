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
        """Load Forge server configuration with fallback"""
        default_config = {
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
                "enable-command-block": True,
                "allow-flight": True
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                user_config = json.load(f)
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except FileNotFoundError:
            self.logger.warning(f"Config file {self.config_path} not found, using defaults")
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        self.config = default_config
    
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
        full_version = f"{mc_version}-{forge_version}"
        
        return f"https://maven.minecraftforge.net/net/minecraftforge/forge/{full_version}/forge-{full_version}-installer.jar"
    
    def download_forge_installer(self):
        """Download Forge installer"""
        installer_url = self.get_forge_download_url()
        self.installer_jar = "server/forge-installer.jar"
        
        self.logger.info(f"Downloading Forge installer from: {installer_url}")
        
        try:
            response = requests.get(installer_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.installer_jar, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            print(f"Download progress: {percent:.1f}%", end='\r')
            
            print()
            file_size = os.path.getsize(self.installer_jar)
            self.logger.info(f"Forge installer downloaded: {file_size} bytes")
            return file_size > 1000000  # Check if file is reasonably sized
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return False
    
    def find_forge_jar(self):
        """Find the forge jar file in various possible locations"""
        server_dir = Path("server")
        
        # Look for forge jar files (new format)
        possible_patterns = [
            "forge-*.jar",
            "libraries/net/minecraftforge/forge/*/forge-*.jar",
            "libraries/net/minecraftforge/forge/*/unix_args.txt"
        ]
        
        for pattern in possible_patterns:
            for file_path in server_dir.glob(pattern):
                if "installer" not in str(file_path) and "universal" not in str(file_path):
                    self.logger.info(f"Found potential forge file: {file_path}")
                    # Check if it's a reasonable size (> 1MB for jar, any size for args file)
                    if file_path.suffix == '.jar':
                        if file_path.stat().st_size > 1000000:
                            return str(file_path)
                    else:
                        return self._create_launch_script()  # Handle new forge format
        
        # If no jar found, check for run scripts
        if (server_dir / "run.sh").exists() or (server_dir / "run.bat").exists():
            self.logger.info("Found run scripts, using new forge format")
            return self._create_launch_script()
        
        return None
    
    def _create_launch_script(self):
        """Create a launch script for the new forge format"""
        self.logger.info("Creating launch script for new Forge format")
        
        # The new forge uses a different launch mechanism
        # We'll create a simple Python launcher
        launch_script = """
import subprocess
import sys
import os

def main():
    # Change to server directory
    os.chdir("server")
    
    # Use the run script if it exists
    if os.path.exists("run.sh"):
        # Make it executable
        os.chmod("run.sh", 0o755)
        # Run with java directly using the args from run.sh
        cmd = ["java", "@user_jvm_args.txt", "@libraries/net/minecraftforge/forge/1.20.1-47.2.0/unix_args.txt", "nogui"]
    else:
        # Fallback to direct java command
        cmd = ["java", "-Xmx4G", "-Xms2G", "-jar", "libraries/net/minecraftforge/forge/1.20.1-47.2.0/forge-1.20.1-47.2.0.jar", "nogui"]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("Server stopped")

if __name__ == "__main__":
    main()
"""
        
        with open("server/launch_forge.py", "w") as f:
            f.write(launch_script)
        
        return "launch_forge.py"
    
    def install_forge_server(self):
        """Install Forge server using the installer"""
        # Download installer if needed
        if not os.path.exists("server/forge-installer.jar"):
            if not self.download_forge_installer():
                return False
        
        self.logger.info("Installing Forge server...")
        
        try:
            # Run the installer
            result = subprocess.run(
                ["java", "-jar", "forge-installer.jar", "--installServer"],
                cwd="server",
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.logger.info("Forge installer completed successfully")
                self.logger.info(f"Installer output: {result.stdout}")
                
                # List all files for debugging
                files = list(Path("server").iterdir())
                self.logger.info(f"Files in server directory: {[f.name for f in files]}")
                
                # Look for the forge jar or launch files
                self.forge_jar = self.find_forge_jar()
                
                if self.forge_jar:
                    self.logger.info(f"Using forge launcher: {self.forge_jar}")
                    return True
                else:
                    self.logger.error("Could not find forge server files after installation")
                    # Try to manually find and set up forge
                    return self._manual_forge_setup()
            else:
                self.logger.error(f"Installer failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Installation error: {e}")
            return False
    
    def _manual_forge_setup(self):
        """Manual setup when automatic detection fails"""
        self.logger.info("Attempting manual forge setup...")
        
        # Check what files we have
        server_files = list(Path("server").iterdir())
        self.logger.info(f"Available files: {[f.name for f in server_files]}")
        
        # If we have run.sh, use that
        if (Path("server") / "run.sh").exists():
            self.logger.info("Using run.sh for server launch")
            self.forge_jar = "run.sh"
            return True
        
        # If we have libraries directory, create a launch script
        if (Path("server") / "libraries").exists():
            self.logger.info("Found libraries directory, creating custom launcher")
            self.forge_jar = self._create_custom_launcher()
            return True
        
        return False
    
    def _create_custom_launcher(self):
        """Create a custom launcher script"""
        launch_content = """#!/bin/bash
cd "$(dirname "$0")"
java -Xmx4G -Xms2G @user_jvm_args.txt @libraries/net/minecraftforge/forge/1.20.1-47.2.0/unix_args.txt "$@"
"""
        
        launch_script = Path("server") / "start_server.sh"
        with open(launch_script, "w") as f:
            f.write(launch_content)
        
        # Make executable
        launch_script.chmod(0o755)
        
        return "start_server.sh"
    
    def setup_server_properties(self):
        """Create server.properties file"""
        properties = self.config["server_properties"]
        
        with open("server/server.properties", "w") as f:
            f.write("# Minecraft server properties\\n")
            f.write("server-port=25565\\n")
            for key, value in properties.items():
                f.write(f"{key}={value}\\n")
        
        # Create eula.txt
        with open("server/eula.txt", "w") as f:
            f.write("eula=true\\n")
        
        self.logger.info("Server properties configured")
    
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
        if not self.forge_jar:
            if not self.install_forge_server():
                return False
        
        self.setup_server_properties()
        self.copy_mods()
        
        self.logger.info(f"Starting Forge server using: {self.forge_jar}")
        
        try:
            if self.forge_jar.endswith('.py'):
                # Python launcher
                self.process = subprocess.Popen(
                    [sys.executable, self.forge_jar],
                    cwd="server",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            elif self.forge_jar.endswith('.sh'):
                # Shell script
                self.process = subprocess.Popen(
                    [f"./{self.forge_jar}", "nogui"],
                    cwd="server",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            else:
                # Direct Java (fallback)
                self.process = subprocess.Popen(
                    ["java", "-Xmx4G", "-Xms2G", "-jar", self.forge_jar, "nogui"],
                    cwd="server",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            
            # Start output monitoring
            output_thread = Thread(target=self._monitor_output, daemon=True)
            output_thread.start()
            
            self.logger.info("Forge server started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def _monitor_output(self):
        """Monitor server output"""
        for line in iter(self.process.stdout.readline, ''):
            if line.strip():
                print(f"[Minecraft] {line.strip()}")
    
    def stop_server(self):
        """Stop the server"""
        if self.process and self.process.poll() is None:
            self.logger.info("Stopping server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=30)
            except:
                self.process.kill()
    
    def is_running(self):
        return self.process and self.process.poll() is None
    
    def get_server_info(self):
        return {
            "running": self.is_running(),
            "version": self.config["minecraft_version"],
            "forge_version": self.config["forge_version"],
            "launcher": self.forge_jar
        }
