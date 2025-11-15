#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def main():
    print("🚀 Simple Forge Server Setup")
    
    # Create directories
    Path("server/mods").mkdir(parents=True, exist_ok=True)
    Path("mods").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Download Forge installer
    print("📥 Downloading Forge installer...")
    url = "https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.2.0/forge-1.20.1-47.2.0-installer.jar"
    
    try:
        import requests
        response = requests.get(url, stream=True, timeout=60)
        with open("server/forge-installer.jar", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("✅ Download complete")
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
        print("✅ Forge installation completed")
        print("📁 Files created:", [f.name for f in Path("server").iterdir()])
    else:
        print("❌ Installation failed")
        print("Error:", result.stderr)
        return
    
    # Create server configuration
    print("⚙️ Configuring server...")
    
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
motd=Forge Server in Codespaces
enable-command-block=true
allow-flight=true
""")
    
    print("✅ Server configured")
    
    # Create simple start script
    with open("start_server.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import subprocess
import os
import sys

print("🎮 Starting Minecraft Forge Server...")
os.chdir("server")

# Try to find and run the server
if os.path.exists("run.sh"):
    print("Using run.sh...")
    subprocess.run(["bash", "run.sh", "nogui"])
elif os.path.exists("run.bat"):
    print("Using run.bat...")
    subprocess.run(["bash", "run.bat", "nogui"])
else:
    # Look for forge jar
    import glob
    jars = glob.glob("forge-*.jar")
    installers = [j for j in jars if "installer" not in j]
    if installers:
        print(f"Using {installers[0]}...")
        subprocess.run(["java", "-Xmx4G", "-Xms2G", "-jar", installers[0], "nogui"])
    else:
        print("❌ No server files found")
        print("Available files:", os.listdir("."))
""")
    
    print("✅ Created start_server.py")
    
    print("\n🎯 SETUP COMPLETE!")
    print("To start the server, run:")
    print("  python start_server.py")
    print("Or manually:")
    print("  cd server && bash run.sh nogui")

if __name__ == "__main__":
    main()