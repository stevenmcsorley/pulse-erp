"""SQLAlchemy models for Inventory Service"""
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Product(Base):
    """Product model - maps to products table"""

    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    product_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, name="metadata")

    # Relationship
    inventory_item: Mapped[Optional["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="product", uselist=False
    )

    __table_args__ = (CheckConstraint("price >= 0", name="positive_price"),)


class InventoryItem(Base):
    """Inventory item model - maps to inventory_items table"""

    __tablename__ = "inventory_items"

    sku: Mapped[str] = mapped_column(
        String(64), ForeignKey("products.sku", ondelete="CASCADE"), primary_key=True
    )
    qty_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationship
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_item")

    __table_args__ = (
        CheckConstraint("qty_on_hand >= 0", name="non_negative_qty"),
        CheckConstraint("reserved_qty >= 0", name="non_negative_reserved"),
        CheckConstraint("reorder_point >= 0", name="non_negative_reorder"),
        CheckConstraint("reserved_qty <= qty_on_hand", name="qty_check"),
    )
