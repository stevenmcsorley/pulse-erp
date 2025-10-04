"""NATS consumer for order_created events"""
import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import InventoryItem
from app.nats_client import nats_client

logger = logging.getLogger(__name__)


class OrderEventConsumer:
    """Consumer for order_created events to auto-reserve stock"""

    def __init__(self):
        self.consumer_name = "inventory-order-consumer"
        self.stream_name = "orders"
        self.subject = "orders.order_created"
        self.processed_orders = set()  # Simple in-memory idempotency tracking

    async def start(self):
        """Start consuming order_created events"""
        if not nats_client.js:
            raise RuntimeError("NATS client not connected")

        try:
            # Create durable consumer
            consumer = await nats_client.js.pull_subscribe(
                subject=self.subject,
                durable=self.consumer_name,
            )

            logger.info(f"Started consuming {self.subject}")

            # Consume messages in loop
            while True:
                try:
                    messages = await consumer.fetch(batch=1, timeout=5)
                    for msg in messages:
                        await self.handle_message(msg)
                        await msg.ack()
                except asyncio.TimeoutError:
                    # No messages available, continue
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise

    async def handle_message(self, msg):
        """Handle a single order_created message"""
        try:
            # Parse message payload
            payload = json.loads(msg.data.decode())
            order_id = payload.get("order_id")
            items = payload.get("items", [])

            logger.info(f"Processing order_created: {order_id}")

            # Check idempotency
            if order_id in self.processed_orders:
                logger.info(f"Order {order_id} already processed (idempotent)")
                return

            # Reserve stock for each item
            async with async_session_maker() as session:
                try:
                    for item in items:
                        await self.reserve_stock_for_item(
                            session, order_id, item["sku"], item["qty"]
                        )

                    await session.commit()
                    self.processed_orders.add(order_id)
                    logger.info(f"Successfully reserved stock for order {order_id}")

                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to reserve stock for order {order_id}: {e}")
                    await self.publish_reservation_failed(order_id, str(e))
                    raise

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise

    async def reserve_stock_for_item(
        self, session: AsyncSession, order_id: str, sku: str, qty: int
    ):
        """Reserve stock for a single order item"""
        # Get inventory with row lock
        result = await session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku).with_for_update()
        )
        inventory = result.scalar_one_or_none()

        if not inventory:
            raise ValueError(f"Product {sku} not found in inventory")

        # Check availability
        available = inventory.qty_on_hand - inventory.reserved_qty
        if available < qty:
            raise ValueError(
                f"Insufficient stock for {sku}. Available: {available}, Requested: {qty}"
            )

        # Reserve stock
        inventory.reserved_qty += qty
        logger.info(f"Reserved {qty} units of {sku} for order {order_id}")

    async def publish_reservation_failed(self, order_id: str, error: str):
        """Publish reservation_failed event"""
        try:
            event = {
                "event_type": "reservation_failed",
                "order_id": order_id,
                "error": error,
            }
            await nats_client.publish("reservation_failed", event)
            logger.info(f"Published reservation_failed for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to publish reservation_failed event: {e}")


# Singleton instance
order_consumer = OrderEventConsumer()
