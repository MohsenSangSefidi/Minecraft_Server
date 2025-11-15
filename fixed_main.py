#!/usr/bin/env python3
import os
import time
import signal
import sys
import subprocess
import threading
from pathlib import Path

class SimpleForgeServer:
    def __init__(self):
        self.process = None
        self.running = False
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = ['server/mods', 'mods', 'logs']
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def find_server_launcher(self):
        """Find how to start the server"""
        server_dir = Path("server")
        
        # Check for run.sh (new Forge format)
        if (server_dir / "run.sh").exists():
            return "run.sh"
        
        # Check for run.bat
        if (server_dir / "run.bat").exists():
            return "run.bat"
        
        # Look for forge jar files (old format)
        forge_jars = list(server_dir.glob("forge-*.jar"))
        # Exclude installer files
        server_jars = [jar for jar in forge_jars if "installer" not in jar.name]
        
        if server_jars:
            return server_jars[0].name
        
        return None
    
    def start_server(self):
        """Start the Minecraft server"""
        launcher = self.find_server_launcher()
        
        if not launcher:
            print("❌ No server launcher found. Please run setup first.")
            return False
        
        print(f"🚀 Starting Minecraft Forge Server using: {launcher}")
        
        try:
            if launcher.endswith('.sh'):
                # Make executable and run
                os.chmod(f"server/{launcher}", 0o755)
                self.process = subprocess.Popen(
                    ["./" + launcher, "nogui"],
                    cwd="server",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            elif launcher.endswith('.jar'):
                # Direct Java execution
                self.process = subprocess.Popen(
                    ["java", "-Xmx4G", "-Xms2G", "-jar", launcher, "nogui"],
                    cwd="server",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            else:
                print(f"❌ Unknown launcher type: {launcher}")
                return False
            
            # Start output monitoring thread
            output_thread = threading.Thread(target=self._monitor_output, daemon=True)
            output_thread.start()
            
            self.running = True
            print("✅ Server started successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def _monitor_output(self):
        """Monitor and print server output"""
        for line in iter(self.process.stdout.readline, ''):
            if line.strip():
                print(f"[Minecraft] {line.strip()}")
                
                # Check for server ready message
                if "Done" in line and "For help" in line:
                    print("🎯 SERVER IS READY! Players can now connect!")
    
    def stop_server(self):
        """Stop the server gracefully"""
        if self.process and self.process.poll() is None:
            print("🛑 Stopping server...")
            try:
                # Try to send stop command
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()
            except:
                # If that fails, terminate
                self.process.terminate()
            
            try:
                self.process.wait(timeout=30)
                print("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️  Server didn't stop, forcing...")
                self.process.kill()
            
            self.running = False
    
    def is_running(self):
        """Check if server is running"""
        return self.process and self.process.poll() is None

def start_web_dashboard():
    """Start a simple web dashboard"""
    try:
        from flask import Flask, render_template_string
        import threading
        
        app = Flask(__name__)
        
        HTML_TEMPLATE = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Minecraft Forge Server</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container { 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                .card { 
                    background: rgba(255,255,255,0.2);
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 10px;
                    border-left: 4px solid #3498db;
                }
                code {
                    background: rgba(0,0,0,0.3);
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎮 Minecraft Forge Server</h1>
                
                <div class="card">
                    <h2>✅ Server Status: RUNNING</h2>
                    <p><strong>Connection Information:</strong></p>
                    <p>Address: <code>localhost:25565</code></p>
                    <p>Version: 1.20.1</p>
                    <p>Forge: 47.2.0</p>
                </div>
                
                <div class="card">
                    <h2>📝 How to Connect</h2>
                    <ol>
                        <li>Open Minecraft Launcher</li>
                        <li>Select Forge 1.20.1 profile</li>
                        <li>Click "Multiplayer"</li>
                        <li>Click "Add Server"</li>
                        <li>Server Address: <code>localhost:25565</code></li>
                        <li>Click "Done" and join!</li>
                    </ol>
                </div>
                
                <div class="card">
                    <h2>🔧 Server Info</h2>
                    <p>This server is running in GitHub Codespaces</p>
                    <p>Check the terminal for server logs and player activity</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        @app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)
        
        @app.route('/status')
        def status():
            return {"status": "running", "version": "1.20.1", "forge": "47.2.0"}
        
        print("🌐 Web Dashboard: http://localhost:8080")
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
        
    except ImportError:
        print("⚠️  Flask not available - web dashboard disabled")
        print("💡 Install with: pip install flask")

def main():
    print("=" * 60)
    print("🎮 MINECRAFT FORGE SERVER")
    print("=" * 60)
    
    server = SimpleForgeServer()
    
    # Check if server is set up
    launcher = server.find_server_launcher()
    if not launcher:
        print("❌ Server not set up. Please run setup first.")
        print("💡 Run: python setup_forge.py")
        return
    
    print(f"🔧 Found server launcher: {launcher}")
    
    # Start web dashboard in background thread
    web_thread = threading.Thread(target=start_web_dashboard, daemon=True)
    web_thread.start()
    
    # Start the server
    if server.start_server():
        print("✅ Server started successfully!")
        print("🌐 Web Dashboard: http://localhost:8080")
        print("🎮 Connect to: localhost:25565")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        try:
            # Keep the main thread alive and monitor server
            while server.running:
                time.sleep(1)
                if not server.is_running():
                    print("⚠️  Server stopped unexpectedly")
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Received stop signal...")
            
        finally:
            server.stop_server()
            
    else:
        print("❌ Failed to start server")

if __name__ == "__main__":
    main()