"""Integration tests for OLAP Worker"""
import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.consumers.event_consumer import OLAPEventConsumer
from app.duckdb_client import DuckDBClient


@pytest.fixture
def duckdb_test_client():
    """Create test DuckDB client with in-memory database"""
    client = DuckDBClient(db_path=":memory:")
    client.connect()
    yield client
    client.close()


@pytest.fixture
def event_consumer(duckdb_test_client):
    """Create test event consumer"""
    with patch("app.consumers.event_consumer.duckdb_client", duckdb_test_client):
        consumer = OLAPEventConsumer()
        yield consumer


@pytest.mark.asyncio
async def test_handle_order_created(event_consumer, duckdb_test_client):
    """Test order_created event processing"""
    payload = {
        "event_id": "evt_001",
        "order_id": "ord_12345",
        "customer_id": "cust_001",
        "total_amount": 150.50,
        "status": "placed",
        "timestamp": "2025-10-04T10:30:00",
    }

    await event_consumer.handle_order_created(payload)

    # Verify event was inserted
    result = duckdb_test_client.conn.execute(
        "SELECT * FROM order_events WHERE order_id = ?", ["ord_12345"]
    ).fetchone()

    assert result is not None
    assert result[1] == "ord_12345"  # order_id
    assert result[2] == "order_created"  # event_type
    assert result[3] == "cust_001"  # customer_id
    assert float(result[4]) == 150.50  # total_amount


@pytest.mark.asyncio
async def test_handle_stock_reserved(event_consumer, duckdb_test_client):
    """Test stock_reserved event processing"""
    payload = {
        "event_id": "evt_002",
        "order_id": "ord_12345",
        "sku": "WIDGET-001",
        "qty_reserved": 5,
        "timestamp": "2025-10-04T10:31:00",
    }

    await event_consumer.handle_stock_reserved(payload)

    # Verify event was inserted
    result = duckdb_test_client.conn.execute(
        "SELECT * FROM stock_events WHERE sku = ?", ["WIDGET-001"]
    ).fetchone()

    assert result is not None
    assert result[1] == "stock_reserved"  # event_type
    assert result[2] == "WIDGET-001"  # sku
    assert result[3] == "ord_12345"  # order_id
    assert result[4] == 5  # qty_reserved


@pytest.mark.asyncio
async def test_handle_invoice_created(event_consumer, duckdb_test_client):
    """Test invoice_created event processing"""
    payload = {
        "event_id": "evt_003",
        "invoice_id": "inv_001",
        "order_id": "ord_12345",
        "amount": 150.50,
        "status": "issued",
        "due_date": "2025-11-03",
        "timestamp": "2025-10-04T10:32:00",
    }

    await event_consumer.handle_invoice_created(payload)

    # Verify event was inserted
    result = duckdb_test_client.conn.execute(
        "SELECT * FROM invoice_events WHERE invoice_id = ?", ["inv_001"]
    ).fetchone()

    assert result is not None
    assert result[1] == "inv_001"  # invoice_id
    assert result[2] == "ord_12345"  # order_id
    assert result[3] == "invoice_created"  # event_type
    assert float(result[4]) == 150.50  # amount


@pytest.mark.asyncio
async def test_sales_aggregate_update(event_consumer, duckdb_test_client):
    """Test sales_by_hour aggregate update"""
    timestamp = datetime(2025, 10, 4, 10, 30, 0)

    # Process two orders in the same hour
    await event_consumer.update_sales_aggregate(timestamp, 100.00)
    await event_consumer.update_sales_aggregate(timestamp, 50.00)

    # Verify aggregate
    hour = timestamp.replace(minute=0, second=0, microsecond=0)
    result = duckdb_test_client.conn.execute(
        "SELECT * FROM sales_by_hour WHERE hour = ?", [hour]
    ).fetchone()

    assert result is not None
    assert result[1] == 2  # total_orders
    assert float(result[2]) == 150.00  # total_revenue
    assert float(result[3]) == 75.00  # avg_order_value


@pytest.mark.asyncio
async def test_idempotent_processing(event_consumer):
    """Test that duplicate events are skipped"""
    # Create mock message
    mock_msg = AsyncMock()
    mock_msg.subject = "orders.order_created"
    mock_msg.data = json.dumps({
        "event_id": "evt_duplicate",
        "order_id": "ord_999",
        "customer_id": "cust_001",
        "total_amount": 100.00,
        "status": "placed",
        "timestamp": "2025-10-04T10:00:00",
    }).encode()

    # Process first time
    await event_consumer.handle_message(mock_msg)
    assert "evt_duplicate" in event_consumer.processed_events

    # Process second time (should skip)
    await event_consumer.handle_message(mock_msg)

    # Verify ack was called both times
    assert mock_msg.ack.call_count == 2


def test_duckdb_schema_initialization(duckdb_test_client):
    """Test DuckDB schema is created correctly"""
    # Check tables exist
    tables = duckdb_test_client.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    table_names = [t[0] for t in tables]

    assert "sales_by_hour" in table_names
    assert "stock_snapshot" in table_names
    assert "ar_aging" in table_names
    assert "order_events" in table_names
    assert "invoice_events" in table_names
    assert "stock_events" in table_names


def test_stock_snapshot_upsert(duckdb_test_client):
    """Test stock snapshot upsert logic"""
    # Insert initial snapshot
    duckdb_test_client.upsert_stock_snapshot(
        sku="WIDGET-001",
        product_name="Blue Widget",
        qty_on_hand=100,
        reserved_qty=10,
        reorder_point=20,
    )

    # Verify
    result = duckdb_test_client.conn.execute(
        "SELECT * FROM stock_snapshot WHERE sku = ?", ["WIDGET-001"]
    ).fetchone()

    assert result is not None
    assert result[0] == "WIDGET-001"
    assert result[2] == 100  # qty_on_hand
    assert result[3] == 10  # reserved_qty
    assert result[4] == 90  # available_qty
    assert result[6] == False  # needs_reorder

    # Update with low stock
    duckdb_test_client.upsert_stock_snapshot(
        sku="WIDGET-001",
        product_name="Blue Widget",
        qty_on_hand=15,
        reserved_qty=5,
        reorder_point=20,
    )

    # Verify reorder flag
    result = duckdb_test_client.conn.execute(
        "SELECT * FROM stock_snapshot WHERE sku = ?", ["WIDGET-001"]
    ).fetchone()

    assert result[2] == 15  # qty_on_hand
    assert result[4] == 10  # available_qty
    assert result[6] == True  # needs_reorder


def test_get_low_stock_items(duckdb_test_client):
    """Test retrieving low stock items"""
    # Insert test data
    duckdb_test_client.upsert_stock_snapshot("WIDGET-001", "Blue Widget", 5, 0, 10)
    duckdb_test_client.upsert_stock_snapshot("WIDGET-002", "Red Widget", 100, 10, 20)

    # Get low stock items
    results = duckdb_test_client.get_low_stock_items()

    assert len(results) == 1
    assert results[0][0] == "WIDGET-001"
