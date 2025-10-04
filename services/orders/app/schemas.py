"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Request schemas
class OrderItemCreate(BaseModel):
    """Schema for creating an order item"""

    sku: str = Field(..., min_length=1, max_length=64, description="Product SKU")
    qty: int = Field(..., gt=0, description="Quantity (must be positive)")
    price: float = Field(..., ge=0, description="Unit price (non-negative)")


class OrderCreate(BaseModel):
    """Schema for creating an order"""

    customer_id: UUID = Field(..., description="Customer UUID")
    items: List[OrderItemCreate] = Field(
        ..., min_length=1, description="Order items (at least one required)"
    )
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional metadata")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("At least one item is required")
        return v


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status"""

    status: str = Field(
        ...,
        pattern="^(draft|placed|cancelled|shipped|completed)$",
        description="New order status",
    )


# Response schemas
class OrderItemResponse(BaseModel):
    """Schema for order item in response"""

    id: UUID
    sku: str
    qty: int
    price: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    """Schema for order in response"""

    id: UUID
    customer_id: UUID
    status: str
    total_amount: float
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
    metadata: dict

    model_config = {"from_attributes": True}


class OrderCreatedEvent(BaseModel):
    """Schema for order_created NATS event payload"""

    event_type: str = "order_created"
    order_id: UUID
    customer_id: UUID
    status: str
    total_amount: float
    items: List[OrderItemResponse]
    created_at: datetime

    model_config = {"from_attributes": True}
