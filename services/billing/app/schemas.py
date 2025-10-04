"""Pydantic schemas for request/response validation"""
from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class InvoiceCreate(BaseModel):
    """Schema for creating an invoice"""

    order_id: UUID = Field(..., description="Order ID to invoice")
    amount: float = Field(..., ge=0, description="Invoice amount")
    due_date: Optional[date] = Field(None, description="Payment due date (optional)")
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional metadata")


# Response schemas
class InvoiceResponse(BaseModel):
    """Schema for invoice in response"""

    id: UUID
    order_id: UUID
    amount: float
    status: str
    issued_at: datetime
    due_date: date
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: dict

    model_config = {"from_attributes": True}


class LedgerEntryResponse(BaseModel):
    """Schema for ledger entry in response"""

    id: UUID
    account: str
    debit: float
    credit: float
    ref_type: str
    ref_id: UUID
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceCreatedEvent(BaseModel):
    """Schema for invoice_created NATS event"""

    event_type: str = "invoice_created"
    invoice_id: UUID
    order_id: UUID
    amount: float
    due_date: date
    timestamp: datetime
