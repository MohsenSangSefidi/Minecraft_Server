#!/usr/bin/env python3
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
