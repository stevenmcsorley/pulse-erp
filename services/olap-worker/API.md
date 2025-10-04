# OLAP Query API Documentation

## Overview

The OLAP Query API provides real-time analytics endpoints for Pulse ERP. Built on FastAPI and DuckDB, it offers sub-second query performance for dashboards and reporting.

**Base URL:** `http://localhost:8004`

**OpenAPI Docs:** `http://localhost:8004/docs`

---

## Authentication

Currently no authentication required (development mode). Production will use JWT tokens from Keycloak.

---

## CORS Configuration

CORS is enabled for all origins in development. Configure `allow_origins` in production.

---

## Endpoints

### Health & Status

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "olap-worker",
  "nats_connected": true,
  "duckdb_connected": true
}
```

#### `GET /stats`

Processing statistics.

**Response:**
```json
{
  "events_processed": 1523,
  "consumer_name": "olap-worker"
}
```

---

### Sales Analytics

#### `GET /query/sales/hourly`

Get hourly sales metrics.

**Parameters:**
- `hours` (query, optional): Number of hours to retrieve (1-168, default: 24)

**Example:**
```bash
curl "http://localhost:8004/query/sales/hourly?hours=48"
```

**Response:**
```json
{
  "hours": 48,
  "data": [
    {
      "hour": "2025-10-04 14:00:00",
      "total_orders": 12,
      "total_revenue": 1250.50,
      "avg_order_value": 104.21,
      "unique_customers": 10,
      "updated_at": "2025-10-04 14:32:15"
    }
  ]
}
```

---

### Inventory Analytics

#### `GET /query/inventory/low-stock`

Get items that need reordering.

**Example:**
```bash
curl "http://localhost:8004/query/inventory/low-stock"
```

**Response:**
```json
{
  "items": [
    {
      "sku": "WIDGET-002",
      "product_name": "Red Widget",
      "qty_on_hand": 5,
      "reserved_qty": 3,
      "available_qty": 2,
      "reorder_point": 10,
      "last_updated": "2025-10-04 14:15:00"
    }
  ]
}
```

#### `GET /query/inventory/movement`

Get stock movement summary.

**Parameters:**
- `limit` (query, optional): Max results (1-500, default: 50)

**Example:**
```bash
curl "http://localhost:8004/query/inventory/movement?limit=20"
```

**Response:**
```json
{
  "items": [
    {
      "sku": "WIDGET-001",
      "total_reservations": 45,
      "total_qty_reserved": 230,
      "first_reservation": "2025-09-15 08:30:00",
      "last_reservation": "2025-10-04 14:20:00"
    }
  ]
}
```

---

### Accounts Receivable

#### `GET /query/ar/overdue`

Get customers with overdue invoices.

**Example:**
```bash
curl "http://localhost:8004/query/ar/overdue"
```

**Response:**
```json
{
  "items": [
    {
      "customer_id": "550e8400-e29b-41d4-a716-446655440001",
      "customer_name": "Acme Corp",
      "total_outstanding": 5000.00,
      "days_30": 2000.00,
      "days_60": 2000.00,
      "days_90_plus": 1000.00,
      "oldest_invoice_date": "2025-08-15",
      "days_overdue": 50
    }
  ]
}
```

---

### Order Analytics

#### `GET /query/orders/daily`

Get daily order volume and revenue.

**Parameters:**
- `days` (query, optional): Number of days (1-365, default: 30)

**Example:**
```bash
curl "http://localhost:8004/query/orders/daily?days=7"
```

**Response:**
```json
{
  "days": 7,
  "data": [
    {
      "order_date": "2025-10-04",
      "total_orders": 45,
      "total_revenue": 4520.00,
      "avg_order_value": 100.44
    }
  ]
}
```

---

### Predefined Queries

#### `POST /query/execute`

Execute a predefined query (prevents SQL injection).

**Request Body:**
```json
{
  "query_name": "sales_24h",
  "limit": 100,
  "params": {}
}
```

**Query Names:**
- `sales_24h` - Hourly sales for last 24 hours
- `sales_7d` - Hourly sales for last 7 days
- `low_stock` - Items needing reorder
- `overdue_ar` - Customers with overdue invoices
- `daily_orders` - Daily order volume
- `stock_movement` - Stock reservation summary
- `top_customers` - Top customers by AR
- `revenue_by_day` - Revenue by day

**Example:**
```bash
curl -X POST "http://localhost:8004/query/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query_name": "sales_24h",
    "limit": 50
  }'
```

**Response:**
```json
{
  "query_name": "sales_24h",
  "columns": ["hour", "total_orders", "total_revenue", "avg_order_value", "unique_customers", "updated_at"],
  "rows": [
    ["2025-10-04 14:00:00", 12, 1250.50, 104.21, 10, "2025-10-04 14:32:15"]
  ],
  "row_count": 24,
  "execution_time_ms": 12.45
}
```

#### `GET /query/available`

List all available predefined queries.

**Example:**
```bash
curl "http://localhost:8004/query/available"
```

**Response:**
```json
{
  "queries": [
    {
      "name": "sales_24h",
      "description": "Hourly sales for last 24 hours",
      "endpoint": "GET /query/sales/hourly?hours=24"
    }
  ]
}
```

---

## Performance

**Expected Response Times (Raspberry Pi 5):**
- Aggregate queries: <50ms
- Event queries: <200ms
- Complex queries: <500ms (p95)

All queries include `execution_time_ms` in the response.

---

## Error Handling

**Standard Error Response:**
```json
{
  "detail": "Error message here"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (invalid query name)
- `422` - Validation error (invalid parameters)
- `500` - Server error (query execution failed)

---

## Security

### SQL Injection Prevention

The API only allows predefined queries. No custom SQL is accepted via the API.

All queries use parameterized placeholders (`?`) to prevent SQL injection.

### Rate Limiting

Not implemented in v1. Add in production.

### Authentication

Development: None
Production: JWT tokens from Keycloak

---

## Usage Examples

### Grafana Data Source

Configure Grafana to use JSON API data source:

```
URL: http://pulse-olap-worker:8004
```

Query example:
```
/query/sales/hourly?hours=168
```

### Frontend Integration

```typescript
// Fetch sales data
const response = await fetch('http://localhost:8004/query/sales/hourly?hours=24');
const data = await response.json();

// Display in chart
chartData = data.data.map(row => ({
  x: new Date(row.hour),
  y: row.total_revenue
}));
```

### Python Analytics

```python
import requests

# Get low stock items
response = requests.get('http://localhost:8004/query/inventory/low-stock')
low_stock = response.json()['items']

# Send alerts
for item in low_stock:
    print(f"Alert: {item['product_name']} needs reorder")
```

---

## Monitoring

All endpoints are automatically monitored by Prometheus (if configured).

Metrics available at: `http://localhost:8004/metrics` (requires prometheus_fastapi_instrumentator)

---

## Development

### Run Locally

```bash
cd services/olap-worker
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

### Run Tests

```bash
pytest tests/test_query_api.py -v
```

### View OpenAPI Docs

Open browser: `http://localhost:8004/docs`

---

## Future Enhancements

- [ ] Query caching with Redis
- [ ] Query result streaming for large datasets
- [ ] CSV/Excel export endpoints
- [ ] Webhook notifications for alerts
- [ ] GraphQL API option
- [ ] WebSocket support for real-time updates
