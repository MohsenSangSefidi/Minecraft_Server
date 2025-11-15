import json
import os
from pathlib import Path


class ConfigLoader:
    @staticmethod
    def load_server_config():
        """Load server configuration with defaults"""
        default_config = {
            "minecraft_version": "1.20.1",
            "forge_version": "47.2.0",
            "memory": {"max": "4G", "min": "2G"},
            "server_properties": {
                "motd": "Forge Server on GitHub Codespaces",
                "max-players": 10,
                "view-distance": 8,
                "online-mode": False,
                "enable-command-block": True
            }
        }

        config_path = "config/server_config.json"
        return ConfigLoader._load_config(config_path, default_config)

    @staticmethod
    def load_gateway_config():
        """Load gateway configuration with defaults"""
        default_config = {
            "dashboard_port": 8080,
            "minecraft_port": 25565
        }

        config_path = "config/gateway_config.json"
        return ConfigLoader._load_config(config_path, default_config)

    @staticmethod
    def load_mods_config():
        """Load mods configuration with defaults"""
        default_config = {
            "auto_download": False,
            "mods": {}
        }

        config_path = "config/mods_config.json"
        return ConfigLoader._load_config(config_path, default_config)

    @staticmethod
    def _load_config(config_path, default_config):
        """Load config from file or create with defaults"""
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Simple merge (for nested dicts, you might want deep merge)
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except FileNotFoundError:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)

        return default_config
