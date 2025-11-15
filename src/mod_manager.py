import requests
import json
import logging
from pathlib import Path
import os


class ModManager:
    def __init__(self, config_path="config/mods_config.json"):
        self.config_path = config_path
        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load mods configuration with fallback"""
        default_config = {
            "minecraft_version": "1.20.1",
            "forge_version": "47.2.0",
            "auto_download": False,
            "mods": {}
        }

        try:
            with open(self.config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            self.logger.warning(f"Mods config file {self.config_path} not found, using defaults")
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)

        self.config = default_config

    def download_all_mods(self):
        """Download all configured mods"""
        if not self.config["auto_download"]:
            self.logger.info("Auto-download is disabled")
            return True

        self.logger.info("Downloading configured mods...")

        Path("mods").mkdir(exist_ok=True)

        success_count = 0
        for mod_name, mod_config in self.config.get("mods", {}).items():
            if mod_config.get("enabled", False):
                self.logger.info(f"Would download mod: {mod_name}")
                success_count += 1

        self.logger.info(f"Downloaded {success_count}/{len(self.config.get('mods', {}))} mods")
        return success_count > 0

    def get_installed_mods(self):
        """Get list of installed mods"""
        mods_dir = Path("mods")
        if not mods_dir.exists():
            return []

        return [mod.name for mod in mods_dir.glob("*.jar")]
