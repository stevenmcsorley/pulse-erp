"""Inventory API endpoints"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Product, InventoryItem
from app.schemas import ProductCreate, ProductResponse, InventoryItemResponse

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
            "metadata": product.metadata,
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
        existing_product.metadata = product_data.metadata

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
            metadata=product_data.metadata,
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
        "metadata": product.metadata,
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
