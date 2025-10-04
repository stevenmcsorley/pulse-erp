"""Orders API endpoints"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Order, OrderItem
from app.nats_client import nats_client
from app.schemas import (
    OrderCreate,
    OrderCreatedEvent,
    OrderResponse,
    OrderStatusUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="Get all orders",
)
async def list_orders(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all orders with their items.

    Returns a list of all orders in the system.
    """
    result = await db.execute(
        select(Order).options(selectinload(Order.items))
    )
    orders = result.scalars().all()
    return orders


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new order with items.

    - **customer_id**: UUID of the customer
    - **items**: List of order items (sku, qty, price)
    - **metadata**: Optional JSONB metadata

    Returns the created order with calculated total_amount.
    Publishes 'order_created' event to NATS.
    """
    # Calculate total amount
    total_amount = sum(item.qty * item.price for item in order_data.items)

    # Create order
    new_order = Order(
        customer_id=order_data.customer_id,
        status="draft",
        total_amount=total_amount,
        metadata=order_data.metadata,
    )

    # Create order items
    for item_data in order_data.items:
        order_item = OrderItem(
            sku=item_data.sku,
            qty=item_data.qty,
            price=item_data.price,
        )
        new_order.items.append(order_item)

    # Save to database
    db.add(new_order)
    await db.flush()  # Get the ID before commit
    await db.refresh(new_order, ["items"])

    # Commit transaction
    await db.commit()

    # Publish event to NATS
    event = OrderCreatedEvent(
        order_id=new_order.id,
        customer_id=new_order.customer_id,
        status=new_order.status,
        total_amount=float(new_order.total_amount),
        items=new_order.items,
        created_at=new_order.created_at,
    )

    try:
        await nats_client.publish("order_created", event.model_dump(mode="json"))
    except Exception as e:
        # Log error but don't fail the request (event publishing is async)
        print(f"Failed to publish order_created event: {e}")

    return new_order


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve an order by its UUID.

    Returns the order with all items included.
    """
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    return order


@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update order status",
)
async def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update the status of an order.

    - **status**: One of: draft, placed, cancelled, shipped, completed

    Returns the updated order.
    """
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    order.status = status_update.status
    await db.commit()
    await db.refresh(order)

    return order
