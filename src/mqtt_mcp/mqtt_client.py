"""MQTT client wrapper module."""

import os
import sys
from typing import Optional
from aiomqtt import Client


class MQTTClient:
    """Simple MQTT client wrapper using aiomqtt."""

    def __init__(self):
        """Initialize client with environment variables."""
        self.host = os.environ.get("MQTT_HOST", "localhost")
        self.port = int(os.environ.get("MQTT_PORT", "1883"))
        self.username = os.environ.get("MQTT_USERNAME")
        self.password = os.environ.get("MQTT_PASSWORD")
        self.client: Optional[Client] = None

    async def connect(self) -> Client:
        """
        Connect to MQTT broker.
        Returns Client instance for use in async context manager.
        """
        try:
            # Create client with or without authentication
            if self.username and self.password:
                client = Client(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )
            else:
                client = Client(
                    hostname=self.host,
                    port=self.port
                )

            sys.stderr.write(f"Connected to MQTT broker at {self.host}:{self.port}\n")
            return client

        except Exception as e:
            error_msg = f"Failed to connect to MQTT broker at {self.host}:{self.port}: {e}"
            sys.stderr.write(f"Error: {error_msg}\n")
            raise ConnectionError(error_msg)

    async def create_client(self, timeout: int = 5) -> Client:
        """
        Create a client instance with optional timeout.
        Used for context manager pattern.
        """
        if self.username and self.password:
            return Client(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=timeout,
                clean_session=True,
                keepalive=60
            )
        else:
            return Client(
                hostname=self.host,
                port=self.port,
                timeout=timeout,
                clean_session=True,
                keepalive=60
            )

    def get_connection_info(self) -> str:
        """Get connection info string for logging."""
        auth = "with auth" if self.username else "without auth"
        return f"{self.host}:{self.port} ({auth})"