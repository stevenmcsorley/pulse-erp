"""NATS Client for OLAP Worker"""
import os
from typing import Optional
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext


class NATSClient:
    """NATS JetStream client wrapper"""

    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.stream_name = os.getenv("NATS_STREAM", "orders")
        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None

    async def connect(self):
        """Connect to NATS server"""
        self.nc = NATS()
        await self.nc.connect(self.nats_url)
        self.js = self.nc.jetstream()
        print(f"Connected to NATS at {self.nats_url}")

    async def close(self):
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            print("NATS connection closed")


# Global client instance
nats_client = NATSClient()
