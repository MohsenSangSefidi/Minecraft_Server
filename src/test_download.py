#!/usr/bin/env python3
import requests
import os
from pathlib import Path

def test_download():
    print("Testing Forge download...")
    
    # Test URL
    url = "https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.2.0/forge-1.20.1-47.2.0-installer.jar"
    
    print(f"Downloading from: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Create server directory
        Path("server").mkdir(exist_ok=True)
        
        # Download file
        file_path = "server/forge-installer.jar"
        total_size = int(response.headers.get('content-length', 0))
        
        with open(file_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"Progress: {percent:.1f}%", end='\r')
        
        print(f"\nDownload complete! File size: {os.path.getsize(file_path)} bytes")
        
        # Test if file is valid
        if os.path.getsize(file_path) > 1000000:  # >1MB
            print("✅ File appears valid")
            return True
        else:
            print("❌ File seems too small")
            return False
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

if __name__ == "__main__":
    test_download()