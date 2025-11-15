#!/usr/bin/env python3
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gateway_manager import GatewayManager
from web_dashboard import WebDashboard
from connection_manager import ConnectionManager
from forge_manager import ForgeManager


def main():
    """Main gateway server entry point"""
    # Setup comprehensive logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/gateway_server.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting Minecraft Gateway Server...")

    try:
        # Initialize managers
        gateway = GatewayManager()
        forge_manager = ForgeManager()

        # Initialize web dashboard with both managers
        dashboard = WebDashboard(gateway, forge_manager)

        # Add connection manager to dashboard
        connection_manager = ConnectionManager(gateway)
        dashboard.app.register_blueprint(connection_manager.blueprint, url_prefix='/api')

        logger.info(f"📊 Gateway server starting on port {gateway.config['gateway_port']}")
        logger.info(f"🌐 Dashboard starting on port {gateway.config['dashboard_port']}")
        logger.info("✅ Gateway system initialized successfully")

        # Start the dashboard (which includes the gateway functionality)
        dashboard.run(
            host='0.0.0.0',
            port=gateway.config['dashboard_port'],
            debug=False
        )

    except Exception as e:
        logger.error(f"❌ Failed to start gateway server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()