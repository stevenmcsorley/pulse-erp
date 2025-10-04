"""SQLAlchemy models for Billing Service"""
from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Invoice(Base):
    """Invoice model - maps to invoices table"""

    __tablename__ = "invoices"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="issued")
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    invoice_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, name="metadata")

    __table_args__ = (
        CheckConstraint(
            "status IN ('issued', 'paid', 'overdue', 'cancelled')", name="valid_status"
        ),
        CheckConstraint("amount >= 0", name="positive_amount"),
    )


class LedgerEntry(Base):
    """Ledger entry model - maps to ledger_entries table"""

    __tablename__ = "ledger_entries"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    account: Mapped[str] = mapped_column(String(64), nullable=False)
    debit: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    credit: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    ref_type: Mapped[str] = mapped_column(String(32), nullable=False)
    ref_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "ref_type IN ('order', 'invoice', 'payment', 'payroll', 'adjustment')",
            name="valid_ref_type",
        ),
        CheckConstraint("debit >= 0", name="non_negative_debit"),
        CheckConstraint("credit >= 0", name="non_negative_credit"),
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)",
            name="ledger_entry_check",
        ),
    )
