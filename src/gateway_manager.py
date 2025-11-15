import socket
import threading
import time
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import select


class GatewayManager:
    def __init__(self, config_path="config/gateway_config.json"):
        self.config_path = config_path
        self.connections = {}
        self.connection_ports = {}
        self.available_ports = set(range(30000, 40000))
        self.used_ports = set()
        self.load_config()
        self.setup_logging()
        self.setup_directories()
        self.forwarding_threads = {}

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/gateway.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load gateway configuration"""
        from config_loader import ConfigLoader
        self.config = ConfigLoader.load_gateway_config()

    def setup_directories(self):
        """Ensure required directories exist"""
        directories = [
            "gateway",
            "gateway/connections",
            "gateway/logs",
            "static",
            "templates",
            "logs"
        ]

        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

    def generate_connection_code(self):
        """Generate a unique connection code"""
        code_length = self.config["connection_code_length"]
        while True:
            code = secrets.token_hex(code_length // 2).upper()[:code_length]
            if code not in self.connections:
                return code

    def allocate_port(self):
        """Allocate an available port for forwarding"""
        if not self.available_ports:
            self.logger.error("No available ports")
            return None

        port = self.available_ports.pop()
        self.used_ports.add(port)
        return port

    def release_port(self, port):
        """Release a port back to available pool"""
        if port in self.used_ports:
            self.used_ports.remove(port)
            self.available_ports.add(port)

    def create_connection(self, user_info=None):
        """Create a new connection entry"""
        connection_code = self.generate_connection_code()
        allocated_port = self.allocate_port()

        if not allocated_port:
            return None

        connection = {
            "code": connection_code,
            "port": allocated_port,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=self.config["connection_timeout"])).isoformat(),
            "user_info": user_info or {},
            "stats": {
                "bytes_forwarded": 0,
                "connections": 0,
                "last_activity": datetime.now().isoformat()
            }
        }

        self.connections[connection_code] = connection
        self.connection_ports[allocated_port] = connection_code

        self.logger.info(f"Created connection {connection_code} on port {allocated_port}")
        self.save_connection_info(connection_code)

        return connection

    def approve_connection(self, connection_code):
        """Approve a pending connection"""
        if connection_code in self.connections:
            self.connections[connection_code]["status"] = "active"
            self.connections[connection_code]["approved_at"] = datetime.now().isoformat()
            self.logger.info(f"Approved connection {connection_code}")
            self.save_connection_info(connection_code)
            return True
        return False

    def revoke_connection(self, connection_code):
        """Revoke a connection"""
        if connection_code in self.connections:
            connection = self.connections[connection_code]
            if connection["port"] in self.forwarding_threads:
                # Stop the forwarding thread
                pass
            self.release_port(connection["port"])
            connection["status"] = "revoked"
            connection["revoked_at"] = datetime.now().isoformat()
            self.logger.info(f"Revoked connection {connection_code}")
            self.save_connection_info(connection_code)
            return True
        return False

    def get_connection_info(self, connection_code):
        """Get connection information"""
        return self.connections.get(connection_code)

    def get_all_connections(self):
        """Get all connections"""
        return self.connections

    def save_connection_info(self, connection_code):
        """Save connection info to file"""
        if connection_code in self.connections:
            connection_file = Path(f"gateway/connections/{connection_code}.json")
            with open(connection_file, 'w') as f:
                json.dump(self.connections[connection_code], f, indent=2)

    def cleanup_expired_connections(self):
        """Clean up expired connections"""
        now = datetime.now()
        expired_codes = []

        for code, connection in self.connections.items():
            expires_at = datetime.fromisoformat(connection["expires_at"])
            if now > expires_at and connection["status"] in ["pending", "active"]:
                expired_codes.append(code)

        for code in expired_codes:
            self.logger.info(f"Cleaning up expired connection {code}")
            self.revoke_connection(code)

    def start_cleanup_thread(self):
        """Start background cleanup thread"""

        def cleanup_worker():
            while True:
                if self.config["auto_cleanup"]:
                    self.cleanup_expired_connections()
                time.sleep(self.config["cleanup_interval"])

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.info("Started connection cleanup thread")

    def start_port_forwarding(self, connection_code):
        """Start port forwarding for a connection"""
        if connection_code not in self.connections:
            return False

        connection = self.connections[connection_code]
        if connection["status"] != "active":
            return False

        # Start TCP forwarding in a separate thread
        forward_thread = threading.Thread(
            target=self._forward_traffic,
            args=(connection["port"], self.config["minecraft_port"]),
            daemon=True
        )
        forward_thread.start()

        self.forwarding_threads[connection["port"]] = forward_thread
        self.logger.info(f"Started forwarding on port {connection['port']} to Minecraft server")
        return True

    def _forward_traffic(self, listen_port, target_port):
        """Forward TCP traffic between ports"""
        try:
            # Create listening socket
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(('0.0.0.0', listen_port))
            listener.listen(5)

            self.logger.info(f"Forwarder listening on port {listen_port}")

            while True:
                try:
                    client_socket, client_addr = listener.accept()
                    self.logger.info(f"New connection from {client_addr} on port {listen_port}")

                    # Connect to Minecraft server
                    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_socket.connect(('localhost', target_port))

                    # Start bidirectional forwarding
                    client_thread = threading.Thread(
                        target=self._forward_socket,
                        args=(client_socket, server_socket, "client->server"),
                        daemon=True
                    )
                    server_thread = threading.Thread(
                        target=self._forward_socket,
                        args=(server_socket, client_socket, "server->client"),
                        daemon=True
                    )

                    client_thread.start()
                    server_thread.start()

                except Exception as e:
                    self.logger.error(f"Error in forwarding: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Failed to start forwarder on port {listen_port}: {e}")

    def _forward_socket(self, source, destination, direction):
        """Forward data between two sockets"""
        try:
            while True:
                # Use select to check if data is available
                readable, _, _ = select.select([source], [], [], 1.0)
                if source in readable:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)

                    # Update statistics
                    # (This would need connection tracking implementation)

        except Exception as e:
            self.logger.debug(f"Socket forwarding error ({direction}): {e}")
        finally:
            try:
                source.close()
            except:
                pass
            try:
                destination.close()
            except:
                pass

    def get_connection_url(self, connection_code):
        """Get connection URL for a code"""
        if connection_code in self.connections:
            connection = self.connections[connection_code]
            if connection["status"] == "active":
                return {
                    "host": "localhost",  # Codespaces will forward this
                    "port": connection["port"],
                    "full_url": f"localhost:{connection['port']}",
                    "connection_code": connection_code
                }
        return None

    def get_connection_stats(self):
        """Get gateway statistics"""
        active_connections = sum(1 for conn in self.connections.values() if conn["status"] == "active")
        total_connections = len(self.connections)

        return {
            "active_connections": active_connections,
            "total_connections": total_connections,
            "available_ports": len(self.available_ports),
            "used_ports": len(self.used_ports)
        }