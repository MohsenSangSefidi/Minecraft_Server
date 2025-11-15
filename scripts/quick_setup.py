#!/usr/bin/env python3
import os
import subprocess
import requests
from pathlib import Path

def main():
    print("🚀 Quick Minecraft Forge Setup")
    
    # Create directories
    Path("server/mods").mkdir(parents=True, exist_ok=True)
    Path("mods").mkdir(exist_ok=True)
    
    # Download Forge if needed
    if not Path("server/forge-installer.jar").exists():
        print("📥 Downloading Forge installer...")
        url = "https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.2.0/forge-1.20.1-47.2.0-installer.jar"
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open("server/forge-installer.jar", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"Progress: {percent:.1f}%", end='\r')
            print("\n✅ Download complete")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return
    
    # Install Forge
    print("🔧 Installing Forge...")
    result = subprocess.run(
        ["java", "-jar", "forge-installer.jar", "--installServer"],
        cwd="server",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Forge installed successfully")
        # List created files
        files = [f.name for f in Path("server").iterdir()]
        print(f"📁 Created files: {files}")
    else:
        print("❌ Installation failed")
        print(f"Error: {result.stderr}")
        return
    
    # Create server files
    print("⚙️  Configuring server...")
    
    # eula.txt
    with open("server/eula.txt", "w") as f:
        f.write("eula=true\n")
    
    # server.properties
    with open("server/server.properties", "w") as f:
        f.write("""# Minecraft server properties
server-port=25565
max-players=10
view-distance=8
online-mode=false
motd=Minecraft Forge Server
enable-command-block=true
allow-flight=true
difficulty=normal
pvp=true
""")
    
    print("✅ Server configured")
    print("\n🎯 SETUP COMPLETE!")
    print("To start the server, run:")
    print("  python fixed_main.py")

if __name__ == "__main__":
    main()
