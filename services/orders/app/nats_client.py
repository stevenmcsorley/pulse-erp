"""NATS JetStream client for event publishing"""
import json
import logging
from typing import Any

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from app.config import settings

logger = logging.getLogger(__name__)


class NATSClient:
    """NATS JetStream client wrapper"""

    def __init__(self):
        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

    async def connect(self):
        """Connect to NATS server and setup JetStream"""
        try:
            self.nc = NATS()
            await self.nc.connect(settings.nats_url)
            self.js = self.nc.jetstream()

            # Ensure stream exists
            try:
                await self.js.stream_info(settings.nats_stream)
                logger.info(f"Connected to existing NATS stream: {settings.nats_stream}")
            except Exception:
                # Create stream if it doesn't exist
                await self.js.add_stream(
                    name=settings.nats_stream,
                    subjects=[f"{settings.nats_stream}.>"],
                )
                logger.info(f"Created NATS stream: {settings.nats_stream}")

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def publish(self, subject: str, data: dict[str, Any]):
        """Publish event to NATS JetStream"""
        if not self.js:
            raise RuntimeError("NATS client not connected")

        try:
            full_subject = f"{settings.nats_stream}.{subject}"
            payload = json.dumps(data, default=str).encode()
            ack = await self.js.publish(full_subject, payload)
            logger.info(f"Published event to {full_subject}: {ack.seq}")
            return ack
        except Exception as e:
            logger.error(f"Failed to publish to {subject}: {e}")
            raise

    async def close(self):
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")


# Singleton instance
nats_client = NATSClient()
