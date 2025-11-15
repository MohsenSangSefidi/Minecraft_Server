import json
import os
from pathlib import Path


class ConfigLoader:
    @staticmethod
    def load_server_config():
        default_config = {
            "minecraft_version": os.getenv("MINECRAFT_VERSION", "1.20.1"),
            "forge_version": os.getenv("FORGE_VERSION", "47.2.0"),
            "memory": {
                "max": os.getenv("SERVER_MAX_MEMORY", "4G"),
                "min": "2G"
            },
            "java_args": [
                "-XX:+UseG1GC",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:MaxGCPauseMillis=100",
                "-XX:+DisableExplicitGC",
                "-XX:TargetSurvivorRatio=90",
                "-XX:G1NewSizePercent=50",
                "-XX:G1MaxNewSizePercent=80",
                "-XX:G1MixedGCLiveThresholdPercent=35",
                "-XX:+AlwaysPreTouch",
                "-XX:+ParallelRefProcEnabled",
                "-Dfml.readTimeout=180"
            ],
            "server_properties": {
                "motd": "Forge Server on GitHub Codespaces",
                "max-players": 10,
                "view-distance": 8,
                "online-mode": False,
                "enable-command-block": True,
                "allow-flight": True,
                "announce-player-achievements": False,
                "difficulty": "normal",
                "pvp": True,
                "spawn-monsters": True,
                "spawn-animals": True,
                "generate-structures": True,
                "max-tick-time": 60000,
                "network-compression-threshold": 256,
                "enable-rcon": True,
                "rcon.port": 25575,
                "rcon.password": "minecraft123"
            }
        }
        return ConfigLoader._load_config("config/server_config.json", default_config)

    @staticmethod
    def load_gateway_config():
        default_config = {
            "gateway_port": 8080,
            "dashboard_port": 8081,
            "admin_port": 3000,
            "minecraft_port": 25565,
            "rcon_port": 25575,
            "max_connections": 50,
            "connection_timeout": 3600,
            "cleanup_interval": 300,
            "require_approval": False,
            "auto_cleanup": True,
            "connection_code_length": 8,
            "allow_quick_join": True,
            "default_connection_duration": 24,
            "rate_limiting": {
                "connections_per_hour": 10,
                "max_connection_duration": 72
            }
        }
        return ConfigLoader._load_config("config/gateway_config.json", default_config)

    @staticmethod
    def load_mods_config():
        default_config = {
            "minecraft_version": "1.20.1",
            "forge_version": "47.2.0",
            "auto_download": False,
            "mods": {
                "jei": {
                    "enabled": True,
                    "project_id": 238222,
                    "file_id": "latest",
                    "description": "Just Enough Items - Item viewing"
                }
            }
        }
        return ConfigLoader._load_config("config/mods_config.json", default_config)

    @staticmethod
    def load_users_config():
        default_config = {
            "allowed_users": [],
            "admin_users": [],
            "banned_ips": [],
            "whitelist": []
        }
        return ConfigLoader._load_config("config/users_config.json", default_config)

    @staticmethod
    def _load_config(config_path, default_config):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Deep merge
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except FileNotFoundError:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)

        return default_config
    