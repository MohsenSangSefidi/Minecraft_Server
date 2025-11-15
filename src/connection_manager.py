import json
import qrcode
import base64
from io import BytesIO
from flask import Blueprint, request, jsonify


class ConnectionManager:
    def __init__(self, gateway_manager):
        self.gateway = gateway_manager
        self.blueprint = Blueprint('connections', __name__)
        self.setup_routes()

    def setup_routes(self):
        """Setup connection management routes"""

        @self.blueprint.route('/connection/generate-qr/<connection_code>')
        def generate_qr(connection_code):
            connection_url = self.gateway.get_connection_url(connection_code)
            if not connection_url:
                return jsonify({"error": "Connection not found"}), 404

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            connection_string = f"{connection_url['host']}:{connection_url['port']}"
            qr.add_data(connection_string)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return jsonify({
                "qr_code": f"data:image/png;base64,{img_str}",
                "connection_string": connection_string
            })

        @self.blueprint.route('/connection/quick-join', methods=['POST'])
        def quick_join():
            """Create a quick connection without approval"""
            # Temporarily disable approval requirement
            original_require_approval = self.gateway.config["require_approval"]
            self.gateway.config["require_approval"] = False

            try:
                connection = self.gateway.create_connection({
                    "name": "Quick Join User",
                    "type": "quick_join"
                })

                if connection:
                    self.gateway.approve_connection(connection["code"])
                    self.gateway.start_port_forwarding(connection["code"])
                    connection_url = self.gateway.get_connection_url(connection["code"])

                    return jsonify({
                        "success": True,
                        "connection": connection,
                        "connection_url": connection_url
                    })
                else:
                    return jsonify({"success": False, "error": "Could not create connection"})

            finally:
                # Restore original setting
                self.gateway.config["require_approval"] = original_require_approval