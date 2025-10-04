"""Integration tests for Inventory API"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

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


@pytest.mark.asyncio
async def test_reserve_stock_success():
    """Test POST /inventory/{sku}/reserve successfully reserves stock"""
    # Create product first
    product_data = {
        "sku": "RESERVE-TEST",
        "name": "Reserve Test Product",
        "price": 10.00,
        "qty_on_hand": 100,
        "reserved_qty": 0,
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/inventory", json=product_data)

        # Reserve stock
        order_id = str(uuid4())
        reservation_data = {"order_id": order_id, "qty": 10}
        reserve_response = await client.post(
            "/inventory/RESERVE-TEST/reserve", json=reservation_data
        )

    assert reserve_response.status_code == 200
    data = reserve_response.json()
    assert data["sku"] == "RESERVE-TEST"
    assert data["order_id"] == order_id
    assert data["qty_reserved"] == 10
    assert data["reserved_qty"] == 10
    assert data["available_qty"] == 90


@pytest.mark.asyncio
async def test_reserve_stock_insufficient():
    """Test POST /inventory/{sku}/reserve returns 409 when insufficient stock"""
    # Create product with limited stock
    product_data = {
        "sku": "LIMITED-STOCK",
        "name": "Limited Stock Product",
        "price": 10.00,
        "qty_on_hand": 5,
        "reserved_qty": 0,
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/inventory", json=product_data)

        # Try to reserve more than available
        order_id = str(uuid4())
        reservation_data = {"order_id": order_id, "qty": 10}
        reserve_response = await client.post(
            "/inventory/LIMITED-STOCK/reserve", json=reservation_data
        )

    assert reserve_response.status_code == 409
    assert "Insufficient stock" in reserve_response.json()["detail"]


@pytest.mark.asyncio
async def test_reserve_stock_not_found():
    """Test POST /inventory/{sku}/reserve returns 404 for non-existent SKU"""
    order_id = str(uuid4())
    reservation_data = {"order_id": order_id, "qty": 10}

    async with AsyncClient(app=app, base_url="http://test") as client:
        reserve_response = await client.post(
            "/inventory/NONEXISTENT/reserve", json=reservation_data
        )

    assert reserve_response.status_code == 404


@pytest.mark.asyncio
async def test_reserve_stock_multiple_reservations():
    """Test multiple reservations update reserved_qty correctly"""
    # Create product
    product_data = {
        "sku": "MULTI-RESERVE",
        "name": "Multi Reserve Product",
        "price": 10.00,
        "qty_on_hand": 100,
        "reserved_qty": 0,
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/inventory", json=product_data)

        # First reservation
        reservation1 = {"order_id": str(uuid4()), "qty": 10}
        response1 = await client.post(
            "/inventory/MULTI-RESERVE/reserve", json=reservation1
        )
        assert response1.status_code == 200
        assert response1.json()["reserved_qty"] == 10

        # Second reservation
        reservation2 = {"order_id": str(uuid4()), "qty": 20}
        response2 = await client.post(
            "/inventory/MULTI-RESERVE/reserve", json=reservation2
        )
        assert response2.status_code == 200
        assert response2.json()["reserved_qty"] == 30
        assert response2.json()["available_qty"] == 70
