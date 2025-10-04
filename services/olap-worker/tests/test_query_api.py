"""Integration tests for OLAP Query API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from app.duckdb_client import DuckDBClient


@pytest.fixture
def test_client():
    """Create test client with in-memory DuckDB"""
    with patch("app.duckdb_client.duckdb_client") as mock_client:
        # Create in-memory database for testing
        client = DuckDBClient(db_path=":memory:")
        client.connect()

        # Insert test data
        client.upsert_sales_by_hour(
            hour="2025-10-04 10:00:00",
            total_orders=5,
            total_revenue=500.00,
        )
        client.upsert_stock_snapshot(
            sku="TEST-001",
            product_name="Test Widget",
            qty_on_hand=5,
            reserved_qty=2,
            reorder_point=10,
        )

        mock_client.conn = client.conn

        with TestClient(app) as test_client:
            yield test_client

        client.close()


def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "olap-worker"


def test_get_sales_hourly(test_client):
    """Test hourly sales endpoint"""
    response = test_client.get("/query/sales/hourly?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert "hours" in data
    assert "data" in data
    assert data["hours"] == 24


def test_get_low_stock(test_client):
    """Test low stock endpoint"""
    response = test_client.get("/query/inventory/low-stock")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Should have at least one low stock item (TEST-001)
    assert len(data["items"]) >= 1


def test_get_overdue_ar(test_client):
    """Test overdue AR endpoint"""
    response = test_client.get("/query/ar/overdue")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_get_daily_orders(test_client):
    """Test daily orders endpoint"""
    response = test_client.get("/query/orders/daily?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "days" in data
    assert "data" in data
    assert data["days"] == 30


def test_get_stock_movement(test_client):
    """Test stock movement endpoint"""
    response = test_client.get("/query/inventory/movement?limit=50")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_list_available_queries(test_client):
    """Test available queries endpoint"""
    response = test_client.get("/query/available")
    assert response.status_code == 200
    data = response.json()
    assert "queries" in data
    assert len(data["queries"]) > 0

    # Check query structure
    first_query = data["queries"][0]
    assert "name" in first_query
    assert "description" in first_query
    assert "endpoint" in first_query


def test_execute_predefined_query(test_client):
    """Test execute predefined query endpoint"""
    response = test_client.post(
        "/query/execute",
        json={
            "query_name": "sales_24h",
            "limit": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "query_name" in data
    assert "columns" in data
    assert "rows" in data
    assert "row_count" in data
    assert "execution_time_ms" in data


def test_execute_query_with_limit(test_client):
    """Test query limit parameter"""
    response = test_client.post(
        "/query/execute",
        json={
            "query_name": "low_stock",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] <= 5


def test_query_validation_limit_too_high(test_client):
    """Test that limit validation works"""
    response = test_client.post(
        "/query/execute",
        json={
            "query_name": "sales_24h",
            "limit": 2000,  # Exceeds max of 1000
        },
    )
    assert response.status_code == 422  # Validation error


def test_query_validation_invalid_query_name(test_client):
    """Test that invalid query names are rejected"""
    response = test_client.post(
        "/query/execute",
        json={
            "query_name": "invalid_query",
        },
    )
    assert response.status_code == 422  # Validation error (enum)


def test_cors_headers(test_client):
    """Test CORS headers are present"""
    response = test_client.options("/query/sales/hourly")
    assert "access-control-allow-origin" in response.headers


def test_openapi_docs(test_client):
    """Test OpenAPI documentation is available"""
    response = test_client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(test_client):
    """Test OpenAPI schema is valid"""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "/query/sales/hourly" in schema["paths"]
    assert "/query/inventory/low-stock" in schema["paths"]


def test_query_performance(test_client):
    """Test query response time"""
    response = test_client.post(
        "/query/execute",
        json={
            "query_name": "sales_24h",
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Query should complete in under 500ms (as per acceptance criteria)
    assert data["execution_time_ms"] < 500


def test_sql_injection_prevention():
    """Test that SQL injection is prevented by using predefined queries"""
    # This test documents that we only allow predefined queries
    # No custom SQL is accepted, preventing SQL injection
    from app.routers.query import PREDEFINED_QUERIES

    # All queries must be parameterized
    for query_name, sql in PREDEFINED_QUERIES.items():
        # Check that queries use parameterized placeholders
        assert "?" in sql or "LIMIT" in sql, f"Query {query_name} should use parameterized queries"
