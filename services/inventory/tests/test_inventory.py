"""Integration tests for Inventory API"""
import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.asyncio
async def test_create_product():
    """Test POST /inventory creates product with inventory"""
    product_data = {
        "sku": "WIDGET-001",
        "name": "Super Widget",
        "description": "A fantastic widget",
        "price": 19.99,
        "qty_on_hand": 100,
        "reserved_qty": 0,
        "reorder_point": 20,
        "metadata": {"category": "widgets"},
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/inventory", json=product_data)

    assert response.status_code == 201
    data = response.json()

    assert data["sku"] == "WIDGET-001"
    assert data["name"] == "Super Widget"
    assert data["price"] == 19.99
    assert data["inventory"]["qty_on_hand"] == 100
    assert data["inventory"]["available_qty"] == 100


@pytest.mark.asyncio
async def test_get_inventory():
    """Test GET /inventory returns all products"""
    # Create a product first
    product_data = {
        "sku": "TEST-SKU",
        "name": "Test Product",
        "price": 10.00,
        "qty_on_hand": 50,
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/inventory", json=product_data)

        # Get all inventory
        get_response = await client.get("/inventory")

    assert get_response.status_code == 200
    data = get_response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Find our test product
    test_product = next((p for p in data if p["sku"] == "TEST-SKU"), None)
    assert test_product is not None
    assert test_product["name"] == "Test Product"


@pytest.mark.asyncio
async def test_update_product():
    """Test POST /inventory updates existing product"""
    sku = "UPDATE-TEST"

    # Create product
    initial_data = {
        "sku": sku,
        "name": "Initial Name",
        "price": 10.00,
        "qty_on_hand": 50,
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/inventory", json=initial_data)
        assert create_response.status_code == 201

        # Update product
        updated_data = {
            "sku": sku,
            "name": "Updated Name",
            "price": 15.00,
            "qty_on_hand": 75,
        }
        update_response = await client.post("/inventory", json=updated_data)

    assert update_response.status_code == 201
    data = update_response.json()
    assert data["name"] == "Updated Name"
    assert data["price"] == 15.00
    assert data["inventory"]["qty_on_hand"] == 75


@pytest.mark.asyncio
async def test_create_product_validation():
    """Test POST /inventory validates request data"""
    invalid_data = {
        "sku": "INVALID",
        "name": "Test",
        "price": -5.00,  # Negative price should fail
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/inventory", json=invalid_data)

    assert response.status_code == 422  # Validation error
