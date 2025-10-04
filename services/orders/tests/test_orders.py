"""Integration tests for Orders API"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from main import app


@pytest.mark.asyncio
async def test_create_order():
    """Test POST /orders creates order and returns 201"""
    customer_id = str(uuid4())
    order_data = {
        "customer_id": customer_id,
        "items": [
            {"sku": "WIDGET-001", "qty": 2, "price": 19.99},
            {"sku": "GADGET-002", "qty": 1, "price": 49.99},
        ],
        "metadata": {"source": "web"},
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/orders", json=order_data)

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["customer_id"] == customer_id
    assert data["status"] == "draft"
    assert data["total_amount"] == 89.97  # (2 * 19.99) + (1 * 49.99)
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_order():
    """Test GET /orders/{id} returns order"""
    # First create an order
    customer_id = str(uuid4())
    order_data = {
        "customer_id": customer_id,
        "items": [{"sku": "TEST-SKU", "qty": 1, "price": 10.00}],
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Get the order
        get_response = await client.get(f"/orders/{order_id}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == order_id
    assert data["customer_id"] == customer_id


@pytest.mark.asyncio
async def test_get_order_not_found():
    """Test GET /orders/{id} returns 404 for non-existent order"""
    non_existent_id = str(uuid4())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/orders/{non_existent_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_order_status():
    """Test PATCH /orders/{id} updates status"""
    # Create order first
    customer_id = str(uuid4())
    order_data = {
        "customer_id": customer_id,
        "items": [{"sku": "TEST-SKU", "qty": 1, "price": 10.00}],
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Update status
        patch_response = await client.patch(
            f"/orders/{order_id}", json={"status": "placed"}
        )

    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["status"] == "placed"


@pytest.mark.asyncio
async def test_create_order_validation():
    """Test POST /orders validates request data"""
    invalid_data = {
        "customer_id": str(uuid4()),
        "items": [],  # Empty items should fail
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/orders", json=invalid_data)

    assert response.status_code == 422  # Validation error
