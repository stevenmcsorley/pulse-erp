"""Billing API endpoints"""
from datetime import datetime, timedelta, date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Invoice, LedgerEntry
from app.nats_client import nats_client
from app.schemas import InvoiceCreate, InvoiceResponse, InvoiceCreatedEvent
from app.config import settings

router = APIRouter()


async def create_ledger_entries(
    session: AsyncSession, invoice: Invoice, description: str
):
    """Create double-entry ledger entries for an invoice"""
    # Debit: Accounts Receivable (asset increase)
    debit_entry = LedgerEntry(
        account="accounts_receivable",
        debit=float(invoice.amount),
        credit=0,
        ref_type="invoice",
        ref_id=invoice.id,
        description=f"{description} - AR debit",
    )
    session.add(debit_entry)

    # Credit: Revenue (income increase)
    credit_entry = LedgerEntry(
        account="revenue",
        debit=0,
        credit=float(invoice.amount),
        ref_type="invoice",
        ref_id=invoice.id,
        description=f"{description} - Revenue credit",
    )
    session.add(credit_entry)


@router.post(
    "/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invoice",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually create an invoice for an order.

    - **order_id**: Order to invoice
    - **amount**: Invoice amount
    - **due_date**: Payment due date (optional, defaults to +30 days)

    Creates invoice and double-entry ledger entries.
    Emits 'invoice_created' event to NATS.
    """
    # Calculate due date if not provided
    due_date = invoice_data.due_date
    if not due_date:
        due_date = (
            datetime.utcnow() + timedelta(days=settings.default_payment_terms_days)
        ).date()

    # Create invoice
    new_invoice = Invoice(
        order_id=invoice_data.order_id,
        amount=invoice_data.amount,
        status="issued",
        issued_at=datetime.utcnow(),
        due_date=due_date,
        metadata=invoice_data.metadata,
    )

    db.add(new_invoice)
    await db.flush()

    # Create ledger entries
    await create_ledger_entries(
        db, new_invoice, f"Invoice for order {invoice_data.order_id}"
    )

    await db.commit()
    await db.refresh(new_invoice)

    # Publish event to NATS
    event = InvoiceCreatedEvent(
        invoice_id=new_invoice.id,
        order_id=new_invoice.order_id,
        amount=float(new_invoice.amount),
        due_date=new_invoice.due_date,
        timestamp=datetime.utcnow(),
    )

    try:
        await nats_client.publish("invoice_created", event.model_dump(mode="json"))
    except Exception as e:
        print(f"Failed to publish invoice_created event: {e}")

    return new_invoice


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice by ID",
)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve an invoice by its UUID.
    """
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return invoice
