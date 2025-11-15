import requests
import json
import logging
from pathlib import Path
import os
from bs4 import BeautifulSoup
import re


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
        """Load mods configuration"""
        from config_loader import ConfigLoader
        self.config = ConfigLoader.load_mods_config()

    def download_mod(self, mod_name, mod_config):
        """Download a mod (simplified - in practice you'd use CurseForge API)"""
        if not mod_config["enabled"]:
            self.logger.info(f"Skipping disabled mod: {mod_name}")
            return False

        self.logger.info(f"Would download mod: {mod_name}")
        # Actual implementation would use CurseForge API with proper authentication
        return True

    def download_all_mods(self):
        """Download all configured mods"""
        if not self.config["auto_download"]:
            return True

        self.logger.info("Downloading configured mods...")

        Path("mods").mkdir(exist_ok=True)

        success_count = 0
        for mod_name, mod_config in self.config["mods"].items():
            if self.download_mod(mod_name, mod_config):
                success_count += 1

        self.logger.info(f"Downloaded {success_count}/{len(self.config['mods'])} mods")
        return success_count > 0

    def get_installed_mods(self):
        """Get list of installed mods"""
        mods_dir = Path("mods")
        if not mods_dir.exists():
            return []

        return [mod.name for mod in mods_dir.glob("*.jar")]