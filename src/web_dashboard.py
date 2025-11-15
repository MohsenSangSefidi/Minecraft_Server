from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit
import json
import secrets
from datetime import datetime
import logging
import os


class WebDashboard:
    def __init__(self, gateway_manager, forge_manager):
        self.gateway = gateway_manager
        self.forge_manager = forge_manager
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_hex(32)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.setup_routes()
        self.setup_socket_handlers()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/dashboard')
        def dashboard():
            return render_template('dashboard.html')

        @self.app.route('/admin')
        def admin():
            return render_template('admin.html')

        @self.app.route('/static/<path:path>')
        def send_static(path):
            return send_from_directory('static', path)

        # API Routes
        @self.app.route('/api/connection/request', methods=['POST'])
        def request_connection():
            data = request.json
            user_info = {
                "name": data.get("name", "Anonymous"),
                "email": data.get("email", ""),
                "purpose": data.get("purpose", "Minecraft")
            }

            connection = self.gateway.create_connection(user_info)

            if connection and not self.gateway.config["require_approval"]:
                self.gateway.approve_connection(connection["code"])
                self.gateway.start_port_forwarding(connection["code"])
                connection_info = self.gateway.get_connection_url(connection["code"])
            else:
                connection_info = None

            return jsonify({
                "success": connection is not None,
                "connection": connection,
                "connection_info": connection_info,
                "requires_approval": self.gateway.config["require_approval"]
            })

        @self.app.route('/api/connection/<connection_code>')
        def get_connection(connection_code):
            connection = self.gateway.get_connection_info(connection_code)
            connection_url = self.gateway.get_connection_url(connection_code)
            return jsonify({
                "connection": connection,
                "connection_url": connection_url
            })

        @self.app.route('/api/connection/<connection_code>/approve', methods=['POST'])
        def approve_connection(connection_code):
            if self.gateway.approve_connection(connection_code):
                self.gateway.start_port_forwarding(connection_code)
                connection_url = self.gateway.get_connection_url(connection_code)
                return jsonify({
                    "success": True,
                    "connection_url": connection_url
                })
            return jsonify({"success": False})

        @self.app.route('/api/connection/<connection_code>/revoke', methods=['POST'])
        def revoke_connection(connection_code):
            success = self.gateway.revoke_connection(connection_code)
            return jsonify({"success": success})

        @self.app.route('/api/connections')
        def get_all_connections():
            connections = self.gateway.get_all_connections()
            return jsonify({"connections": connections})

        @self.app.route('/api/server/status')
        def server_status():
            server_info = self.forge_manager.get_server_info()
            return jsonify({
                "status": "running" if server_info["running"] else "stopped",
                "players_online": 0,  # You would implement player tracking
                "max_players": self.forge_manager.config["server_properties"]["max-players"],
                "version": server_info["minecraft_version"],
                "forge_version": server_info["forge_version"],
                "mods_count": server_info["mods_count"]
            })

        @self.app.route('/api/gateway/stats')
        def gateway_stats():
            stats = self.gateway.get_connection_stats()
            return jsonify(stats)

        @self.app.route('/api/server/command', methods=['POST'])
        def send_server_command():
            if not self.forge_manager.is_running():
                return jsonify({"success": False, "error": "Server not running"})

            data = request.json
            command = data.get("command", "")

            if command:
                # This would use RCON or other method to send commands
                result = self.forge_manager.send_rcon_command(command)
                return jsonify({"success": True, "result": result})

            return jsonify({"success": False, "error": "No command provided"})

    def setup_socket_handlers(self):
        """Setup Socket.IO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            logging.info('Client connected')
            # Send initial data
            emit('connections_update', {
                'connections': self.gateway.get_all_connections()
            })
            emit('server_status', {
                'status': 'running' if self.forge_manager.is_running() else 'stopped'
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logging.info('Client disconnected')

        @self.socketio.on('request_connection')
        def handle_connection_request(data):
            connection = self.gateway.create_connection(data)
            emit('connection_created', {'connection': connection}, broadcast=True)

        @self.socketio.on('approve_connection')
        def handle_approve_connection(data):
            connection_code = data.get('connection_code')
            if self.gateway.approve_connection(connection_code):
                self.gateway.start_port_forwarding(connection_code)
                connection_url = self.gateway.get_connection_url(connection_code)
                emit('connection_approved', {
                    'connection_code': connection_code,
                    'connection_url': connection_url
                }, broadcast=True)

    def run(self, host='0.0.0.0', port=8081, debug=False):
        """Run the web dashboard"""
        self.gateway.start_cleanup_thread()
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)