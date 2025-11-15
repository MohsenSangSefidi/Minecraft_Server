# 🎮 Forge Minecraft Server with Custom Gateway

A complete Minecraft Forge server setup with a custom gateway system for GitHub Codespaces.

## ✨ Features

- **Forge Mod Support**: Full Forge modding platform support
- **Custom Gateway**: Ngrok-like connection system without external dependencies
- **Web Dashboard**: Beautiful web interface for server management
- **Connection Management**: Create, approve, and manage player connections
- **Real-time Monitoring**: Live server status and connection tracking
- **QR Code Support**: Easy mobile device connections
- **Auto-setup**: Automatic Forge installation and configuration

## 🚀 Quick Start

### 1. Setup in GitHub Codespaces

1. Create a new repository with these files
2. Open in GitHub Codespaces
3. The server will auto-setup on first launch

### 2. Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup Forge server
python scripts/setup_forge.py

# Start the complete system
python main.py