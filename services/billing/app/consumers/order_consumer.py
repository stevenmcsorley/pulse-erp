"""NATS consumer for order_created events to auto-generate invoices"""
import asyncio
import json
import logging
from datetime import datetime, timedelta

from app.database import async_session_maker
from app.models import Invoice, LedgerEntry
from app.nats_client import nats_client
from app.config import settings

logger = logging.getLogger(__name__)


class OrderEventConsumer:
    """Consumer for order_created events to auto-generate invoices"""

    def __init__(self):
        self.consumer_name = "billing-order-consumer"
        self.stream_name = "orders"
        self.subject = "orders.order_created"
        self.processed_orders = set()  # Idempotency tracking

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
            payload = json.loads(msg.data.decode())
            order_id = payload.get("order_id")
            total_amount = payload.get("total_amount")

            logger.info(f"Processing order_created for invoice: {order_id}")

            # Check idempotency
            if order_id in self.processed_orders:
                logger.info(f"Order {order_id} already processed (idempotent)")
                return

            # Create invoice
            async with async_session_maker() as session:
                try:
                    # Calculate due date
                    due_date = (
                        datetime.utcnow()
                        + timedelta(days=settings.default_payment_terms_days)
                    ).date()

                    # Create invoice
                    invoice = Invoice(
                        order_id=order_id,
                        amount=total_amount,
                        status="issued",
                        issued_at=datetime.utcnow(),
                        due_date=due_date,
                        metadata={"auto_generated": True},
                    )
                    session.add(invoice)
                    await session.flush()

                    # Create ledger entries (double-entry)
                    await self.create_ledger_entries(session, invoice, order_id)

                    await session.commit()
                    self.processed_orders.add(order_id)

                    logger.info(
                        f"Auto-generated invoice {invoice.id} for order {order_id}"
                    )

                    # Publish invoice_created event
                    await self.publish_invoice_created(invoice)

                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to create invoice for order {order_id}: {e}")
                    raise

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise

    async def create_ledger_entries(self, session, invoice, order_id):
        """Create double-entry ledger entries"""
        # Debit AR
        debit_entry = LedgerEntry(
            account="accounts_receivable",
            debit=float(invoice.amount),
            credit=0,
            ref_type="invoice",
            ref_id=invoice.id,
            description=f"Invoice for order {order_id} - AR debit",
        )
        session.add(debit_entry)

        # Credit Revenue
        credit_entry = LedgerEntry(
            account="revenue",
            debit=0,
            credit=float(invoice.amount),
            ref_type="invoice",
            ref_id=invoice.id,
            description=f"Invoice for order {order_id} - Revenue credit",
        )
        session.add(credit_entry)

    async def publish_invoice_created(self, invoice):
        """Publish invoice_created event"""
        try:
            event = {
                "event_type": "invoice_created",
                "invoice_id": str(invoice.id),
                "order_id": str(invoice.order_id),
                "amount": float(invoice.amount),
                "due_date": invoice.due_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            await nats_client.publish("invoice_created", event)
            logger.info(f"Published invoice_created for {invoice.id}")
        except Exception as e:
            logger.error(f"Failed to publish invoice_created event: {e}")


# Singleton instance
order_consumer = OrderEventConsumer()
