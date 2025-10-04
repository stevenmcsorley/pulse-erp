"""OLAP Event Consumer - Processes domain events and materializes to DuckDB"""
import json
import asyncio
from datetime import datetime
from typing import Set
from nats.js.api import ConsumerConfig, AckPolicy

from app.nats_client import nats_client
from app.duckdb_client import duckdb_client


class OLAPEventConsumer:
    """Consumes all domain events and materializes to DuckDB OLAP tables"""

    def __init__(self):
        self.processed_events: Set[str] = set()  # Idempotency tracking
        self.consumer_name = "olap-worker"

    async def start(self):
        """Start consuming events from all subjects"""
        print("Starting OLAP event consumer...")

        # Subscribe to all order-related events
        subjects = [
            "orders.order_created",
            "orders.order_updated",
            "orders.stock_reserved",
            "orders.reservation_failed",
            "orders.invoice_created",
        ]

        # Create durable pull-based consumer
        try:
            consumer_config = ConsumerConfig(
                durable_name=self.consumer_name,
                ack_policy=AckPolicy.EXPLICIT,
                filter_subjects=subjects,
            )

            consumer = await nats_client.js.pull_subscribe_bind(
                durable=self.consumer_name,
                stream=nats_client.stream_name,
                config=consumer_config,
            )

            print(f"Subscribed to subjects: {subjects}")

            # Continuously fetch and process messages
            while True:
                try:
                    # Fetch up to 10 messages with 5 second timeout
                    messages = await consumer.fetch(batch=10, timeout=5)

                    for msg in messages:
                        await self.handle_message(msg)

                except asyncio.TimeoutError:
                    # No messages available, continue polling
                    continue
                except Exception as e:
                    print(f"Error fetching messages: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            print(f"Error setting up consumer: {e}")
            raise

    async def handle_message(self, msg):
        """Process a single NATS message"""
        try:
            subject = msg.subject
            payload = json.loads(msg.data.decode())
            event_id = payload.get("event_id", f"{subject}:{payload.get('order_id', 'unknown')}")

            # Idempotency check
            if event_id in self.processed_events:
                print(f"Skipping duplicate event: {event_id}")
                await msg.ack()
                return

            print(f"Processing event: {subject} - {event_id}")

            # Route to appropriate handler
            if subject == "orders.order_created":
                await self.handle_order_created(payload)
            elif subject == "orders.order_updated":
                await self.handle_order_updated(payload)
            elif subject == "orders.stock_reserved":
                await self.handle_stock_reserved(payload)
            elif subject == "orders.reservation_failed":
                await self.handle_reservation_failed(payload)
            elif subject == "orders.invoice_created":
                await self.handle_invoice_created(payload)
            else:
                print(f"Unknown event type: {subject}")

            # Mark as processed
            self.processed_events.add(event_id)
            await msg.ack()

            print(f"Successfully processed: {event_id}")

        except Exception as e:
            print(f"Error handling message: {e}")
            # Don't ack on error - message will be redelivered
            await msg.nak()

    async def handle_order_created(self, payload: dict):
        """Handle order_created event"""
        order_id = payload.get("order_id")
        customer_id = payload.get("customer_id")
        total_amount = payload.get("total_amount", 0)
        status = payload.get("status", "placed")
        event_timestamp = datetime.fromisoformat(payload.get("timestamp"))

        # Insert raw event
        duckdb_client.insert_order_event(
            order_id=order_id,
            event_type="order_created",
            customer_id=customer_id,
            total_amount=total_amount,
            status=status,
            event_timestamp=event_timestamp,
        )

        # Update sales_by_hour aggregate
        await self.update_sales_aggregate(event_timestamp, total_amount)

    async def handle_order_updated(self, payload: dict):
        """Handle order_updated event"""
        order_id = payload.get("order_id")
        customer_id = payload.get("customer_id")
        total_amount = payload.get("total_amount", 0)
        status = payload.get("status")
        event_timestamp = datetime.fromisoformat(payload.get("timestamp"))

        # Insert raw event
        duckdb_client.insert_order_event(
            order_id=order_id,
            event_type="order_updated",
            customer_id=customer_id,
            total_amount=total_amount,
            status=status,
            event_timestamp=event_timestamp,
        )

    async def handle_stock_reserved(self, payload: dict):
        """Handle stock_reserved event"""
        order_id = payload.get("order_id")
        sku = payload.get("sku")
        qty_reserved = payload.get("qty_reserved", 0)
        event_timestamp = datetime.fromisoformat(payload.get("timestamp"))

        # Insert raw event
        duckdb_client.insert_stock_event(
            event_type="stock_reserved",
            sku=sku,
            order_id=order_id,
            qty_reserved=qty_reserved,
            event_timestamp=event_timestamp,
        )

        # Update stock snapshot
        # Note: In production, you'd query OLTP database for current inventory levels
        # For now, we'll just log the reservation
        print(f"Stock reserved: {sku} - {qty_reserved} units for order {order_id}")

    async def handle_reservation_failed(self, payload: dict):
        """Handle reservation_failed event"""
        order_id = payload.get("order_id")
        sku = payload.get("sku")
        reason = payload.get("reason", "insufficient_stock")
        event_timestamp = datetime.fromisoformat(payload.get("timestamp"))

        # Insert raw event
        duckdb_client.insert_stock_event(
            event_type="reservation_failed",
            sku=sku,
            order_id=order_id,
            qty_reserved=0,
            event_timestamp=event_timestamp,
        )

        print(f"Reservation failed: {sku} for order {order_id} - {reason}")

    async def handle_invoice_created(self, payload: dict):
        """Handle invoice_created event"""
        invoice_id = payload.get("invoice_id")
        order_id = payload.get("order_id")
        amount = payload.get("amount", 0)
        status = payload.get("status", "issued")
        due_date = payload.get("due_date")
        event_timestamp = datetime.fromisoformat(payload.get("timestamp"))

        # Insert raw event
        duckdb_client.insert_invoice_event(
            invoice_id=invoice_id,
            order_id=order_id,
            event_type="invoice_created",
            amount=amount,
            status=status,
            due_date=due_date,
            event_timestamp=event_timestamp,
        )

        print(f"Invoice created: {invoice_id} for order {order_id} - ${amount}")

    async def update_sales_aggregate(self, event_timestamp: datetime, order_amount: float):
        """Update sales_by_hour aggregate table"""
        # Truncate timestamp to hour
        hour = event_timestamp.replace(minute=0, second=0, microsecond=0)

        # In production, you'd query DuckDB for existing values
        # For now, we'll use a simple increment approach
        result = duckdb_client.conn.execute("""
            SELECT total_orders, total_revenue
            FROM sales_by_hour
            WHERE hour = ?
        """, [hour]).fetchone()

        if result:
            total_orders = result[0] + 1
            total_revenue = result[1] + order_amount
        else:
            total_orders = 1
            total_revenue = order_amount

        duckdb_client.upsert_sales_by_hour(hour, total_orders, total_revenue)


# Global consumer instance
olap_consumer = OLAPEventConsumer()
