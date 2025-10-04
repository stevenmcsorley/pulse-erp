"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class ProductCreate(BaseModel):
    """Schema for creating/updating a product"""

    sku: str = Field(..., min_length=1, max_length=64, description="Product SKU")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Unit price (non-negative)")
    qty_on_hand: int = Field(0, ge=0, description="Quantity on hand")
    reserved_qty: int = Field(0, ge=0, description="Reserved quantity")
    reorder_point: int = Field(0, ge=0, description="Reorder point threshold")
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional metadata")


class StockReservationRequest(BaseModel):
    """Schema for reserving stock"""

    order_id: UUID = Field(..., description="Order ID requesting reservation")
    qty: int = Field(..., gt=0, description="Quantity to reserve (must be positive)")


class StockReservationResponse(BaseModel):
    """Schema for stock reservation response"""

    sku: str
    order_id: UUID
    qty_reserved: int
    qty_on_hand: int
    reserved_qty: int
    available_qty: int
    message: str


class StockReservedEvent(BaseModel):
    """Schema for stock_reserved NATS event"""

    event_type: str = "stock_reserved"
    sku: str
    order_id: UUID
    qty: int
    timestamp: datetime


# Response schemas
class InventoryItemResponse(BaseModel):
    """Schema for inventory item in response"""

    sku: str
    qty_on_hand: int
    reserved_qty: int
    reorder_point: int
    available_qty: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    """Schema for product in response"""

    sku: str
    name: str
    description: Optional[str]
    price: float
    created_at: datetime
    updated_at: datetime
    metadata: dict
    inventory: Optional[InventoryItemResponse] = None

    model_config = {"from_attributes": True}
