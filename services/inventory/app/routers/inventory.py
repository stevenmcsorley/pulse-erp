"""Inventory API endpoints"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Product, InventoryItem
from app.nats_client import nats_client
from app.schemas import (
    ProductCreate,
    ProductResponse,
    InventoryItemResponse,
    StockReservationRequest,
    StockReservationResponse,
    StockReservedEvent,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="Get all products with inventory",
)
async def get_inventory(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all products with their inventory levels.

    Returns a list of products with stock information.
    """
    result = await db.execute(
        select(Product).options(selectinload(Product.inventory_item))
    )
    products = result.scalars().all()

    # Transform to response format with calculated available_qty
    response = []
    for product in products:
        product_dict = {
            "sku": product.sku,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "metadata": product.product_metadata,
        }

        if product.inventory_item:
            inv = product.inventory_item
            product_dict["inventory"] = {
                "sku": inv.sku,
                "qty_on_hand": inv.qty_on_hand,
                "reserved_qty": inv.reserved_qty,
                "reorder_point": inv.reorder_point,
                "available_qty": inv.qty_on_hand - inv.reserved_qty,
                "updated_at": inv.updated_at,
            }
        else:
            product_dict["inventory"] = None

        response.append(product_dict)

    return response


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update product and inventory",
)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new product with inventory or update existing.

    - **sku**: Unique product identifier
    - **name**: Product name
    - **price**: Unit price (must be >= 0)
    - **qty_on_hand**: Initial stock quantity
    - **reorder_point**: Minimum stock level threshold

    Returns the created/updated product with inventory.
    """
    # Check if product exists
    result = await db.execute(
        select(Product).where(Product.sku == product_data.sku)
    )
    existing_product = result.scalar_one_or_none()

    if existing_product:
        # Update existing product
        existing_product.name = product_data.name
        existing_product.description = product_data.description
        existing_product.price = product_data.price
        existing_product.product_metadata = product_data.metadata

        # Update inventory if exists
        if existing_product.inventory_item:
            existing_product.inventory_item.qty_on_hand = product_data.qty_on_hand
            existing_product.inventory_item.reserved_qty = product_data.reserved_qty
            existing_product.inventory_item.reorder_point = product_data.reorder_point
        else:
            # Create inventory item for existing product
            new_inventory = InventoryItem(
                sku=product_data.sku,
                qty_on_hand=product_data.qty_on_hand,
                reserved_qty=product_data.reserved_qty,
                reorder_point=product_data.reorder_point,
            )
            db.add(new_inventory)

        product = existing_product
    else:
        # Create new product
        new_product = Product(
            sku=product_data.sku,
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            product_metadata=product_data.metadata,
        )
        db.add(new_product)

        # Create inventory item
        new_inventory = InventoryItem(
            sku=product_data.sku,
            qty_on_hand=product_data.qty_on_hand,
            reserved_qty=product_data.reserved_qty,
            reorder_point=product_data.reorder_point,
        )
        db.add(new_inventory)

        product = new_product

    await db.commit()
    await db.refresh(product, ["inventory_item"])

    # Format response
    response = {
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "metadata": product.product_metadata,
    }

    if product.inventory_item:
        inv = product.inventory_item
        response["inventory"] = {
            "sku": inv.sku,
            "qty_on_hand": inv.qty_on_hand,
            "reserved_qty": inv.reserved_qty,
            "reorder_point": inv.reorder_point,
            "available_qty": inv.qty_on_hand - inv.reserved_qty,
            "updated_at": inv.updated_at,
        }

    return response


@router.get(
    "/{sku}",
    response_model=ProductResponse,
    summary="Get a single product by SKU with inventory",
)
async def get_product_by_sku(
    sku: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single product by its SKU with its inventory levels.

    - **sku**: The SKU of the product to retrieve.

    Returns the product with stock information or 404 if not found.
    """
    result = await db.execute(
        select(Product).options(selectinload(Product.inventory_item)).where(Product.sku == sku)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with SKU {sku} not found",
        )

    # Transform to response format with calculated available_qty
    response = {
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "metadata": product.product_metadata,
    }

    if product.inventory_item:
        inv = product.inventory_item
        response["inventory"] = {
            "sku": inv.sku,
            "qty_on_hand": inv.qty_on_hand,
            "reserved_qty": inv.reserved_qty,
            "reorder_point": inv.reorder_point,
            "available_qty": inv.qty_on_hand - inv.reserved_qty,
            "updated_at": inv.updated_at,
        }
    else:
        response["inventory"] = None

    return response


@router.put(
    "/{sku}",
    response_model=ProductResponse,
    summary="Update an existing product and inventory by SKU",
)
async def update_product(
    sku: str,
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing product and its inventory levels.

    - **sku**: Product SKU to update
    - **product_data**: Updated product and inventory data

    Returns the updated product with inventory or 404 if not found.
    """
    result = await db.execute(
        select(Product).options(selectinload(Product.inventory_item)).where(Product.sku == sku)
    )
    existing_product = result.scalar_one_or_none()

    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with SKU {sku} not found",
        )

    # Update product fields
    existing_product.name = product_data.name
    existing_product.description = product_data.description
    existing_product.price = product_data.price
    existing_product.product_metadata = product_data.metadata

    # Update inventory if exists, otherwise create it
    if existing_product.inventory_item:
        existing_product.inventory_item.qty_on_hand = product_data.qty_on_hand
        existing_product.inventory_item.reserved_qty = product_data.reserved_qty
        existing_product.inventory_item.reorder_point = product_data.reorder_point
    else:
        new_inventory = InventoryItem(
            sku=product_data.sku,
            qty_on_hand=product_data.qty_on_hand,
            reserved_qty=product_data.reserved_qty,
            reorder_point=product_data.reorder_point,
        )
        db.add(new_inventory)

    await db.commit()
    await db.refresh(existing_product, ["inventory_item"])

    # Format response
    response = {
        "sku": existing_product.sku,
        "name": existing_product.name,
        "description": existing_product.description,
        "price": float(existing_product.price),
        "created_at": existing_product.created_at,
        "updated_at": existing_product.updated_at,
        "metadata": existing_product.product_metadata,
    }

    if existing_product.inventory_item:
        inv = existing_product.inventory_item
        response["inventory"] = {
            "sku": inv.sku,
            "qty_on_hand": inv.qty_on_hand,
            "reserved_qty": inv.reserved_qty,
            "reorder_point": inv.reorder_point,
            "available_qty": inv.qty_on_hand - inv.reserved_qty,
            "updated_at": inv.updated_at,
        }
    else:
        response["inventory"] = None

    return response


@router.patch(
    "/{sku}/adjust-stock",
    response_model=InventoryItemResponse,
    summary="Adjust stock quantity for a product",
)
async def adjust_stock(
    sku: str,
    adjustment: int = Body(..., embed=True, description="Amount to adjust stock by (can be positive or negative)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Adjust the quantity on hand for a specific product.

    - **sku**: The SKU of the product to adjust stock for.
    - **adjustment**: The amount to adjust the stock by (positive to increase, negative to decrease).

    Returns the updated inventory item or 404 if not found.
    """
    result = await db.execute(
        select(InventoryItem).where(InventoryItem.sku == sku).with_for_update()
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item for SKU {sku} not found",
        )

    new_qty_on_hand = inventory.qty_on_hand + adjustment
    if new_qty_on_hand < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment would result in negative stock",
        )

    inventory.qty_on_hand = new_qty_on_hand
    await db.commit()
    await db.refresh(inventory)

    return inventory


@router.post(
    "/{sku}/reserve",
    response_model=StockReservationResponse,
    summary="Reserve stock for an order",
)
async def reserve_stock(
    sku: str,
    reservation: StockReservationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Atomically reserve stock for an order.

    - **sku**: Product SKU to reserve
    - **order_id**: Order ID requesting reservation
    - **qty**: Quantity to reserve

    Returns reservation confirmation or 409 if insufficient stock.
    Emits 'stock_reserved' event to NATS on success.
    """
    # Get inventory item with row-level lock
    result = await db.execute(
        select(InventoryItem).where(InventoryItem.sku == sku).with_for_update()
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {sku} not found in inventory",
        )

    # Check if sufficient stock available
    available = inventory.qty_on_hand - inventory.reserved_qty
    if available < reservation.qty:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient stock for {sku}. Available: {available}, Requested: {reservation.qty}",
        )

    # Reserve stock atomically
    inventory.reserved_qty += reservation.qty

    await db.commit()
    await db.refresh(inventory)

    # Publish event to NATS
    event = StockReservedEvent(
        sku=sku,
        order_id=reservation.order_id,
        qty=reservation.qty,
        timestamp=datetime.utcnow(),
    )

    try:
        await nats_client.publish("stock_reserved", event.model_dump(mode="json"))
    except Exception as e:
        print(f"Failed to publish stock_reserved event: {e}")

    # Build response
    return StockReservationResponse(
        sku=sku,
        order_id=reservation.order_id,
        qty_reserved=reservation.qty,
        qty_on_hand=inventory.qty_on_hand,
        reserved_qty=inventory.reserved_qty,
        available_qty=inventory.qty_on_hand - inventory.reserved_qty,
        message=f"Successfully reserved {reservation.qty} units of {sku}",
    )
