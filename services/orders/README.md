# Orders Service

FastAPI microservice for order management in Pulse ERP.

## Features

- **POST /orders** - Create new orders with items
- **GET /orders/{id}** - Retrieve order by ID
- **PATCH /orders/{id}** - Update order status
- **Event Publishing** - Publishes `order_created` events to NATS JetStream
- **Database Transactions** - Atomic order + items creation
- **Async/Await** - Full async support with asyncpg and SQLAlchemy 2.0

## Tech Stack

- **Framework**: FastAPI 0.115
- **Database**: PostgreSQL with asyncpg driver
- **ORM**: SQLAlchemy 2.0 (async)
- **Messaging**: NATS JetStream
- **Testing**: pytest + pytest-asyncio
- **Validation**: Pydantic v2

## Project Structure

```
services/orders/
├── app/
│   ├── __init__.py
│   ├── config.py          # Settings & environment variables
│   ├── database.py        # DB engine, session factory
│   ├── models.py          # SQLAlchemy models (Order, OrderItem)
│   ├── schemas.py         # Pydantic schemas for validation
│   ├── nats_client.py     # NATS JetStream client
│   └── routers/
│       ├── __init__.py
│       └── orders.py      # Order endpoints
├── tests/
│   ├── __init__.py
│   └── test_orders.py     # Integration tests
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── Dockerfile             # Multi-stage Docker build
├── pytest.ini             # Pytest configuration
└── README.md              # This file
```

## Environment Variables

```bash
DB_HOST=postgres
DB_PORT=5432
POSTGRES_DB=pulse_erp
POSTGRES_USER=pulseadmin
POSTGRES_PASSWORD=changeme
NATS_URL=nats://nats:4222
NATS_STREAM=orders
SERVICE_NAME=orders-service
SERVICE_PORT=8001
```

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- NATS Server with JetStream

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_HOST=localhost
export POSTGRES_PASSWORD=your_password
export NATS_URL=nats://localhost:4222

# Run migrations first (from project root)
./migrations/migrate.sh up

# Run the service
uvicorn main:app --reload --port 8001
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_orders.py::test_create_order -v
```

## Docker Deployment

### Build Image

```bash
# Build for arm64 (Raspberry Pi 5)
docker buildx build --platform linux/arm64 -t pulse-orders:latest .

# Build for amd64 (development)
docker buildx build --platform linux/amd64 -t pulse-orders:latest .
```

### Run with Docker Compose

```bash
# Start infrastructure first
docker compose -f docker-compose.base.yml up -d

# Run migrations
./migrations/migrate.sh up

# Start Orders service
docker compose -f docker-compose.services.yml up -d orders

# View logs
docker compose -f docker-compose.services.yml logs -f orders
```

## API Examples

### Create Order

```bash
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "550e8400-e29b-41d4-a716-446655440000",
    "items": [
      {"sku": "WIDGET-001", "qty": 2, "price": 19.99},
      {"sku": "GADGET-002", "qty": 1, "price": 49.99}
    ],
    "metadata": {"source": "web"}
  }'
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "total_amount": 89.97,
  "items": [
    {
      "id": "...",
      "sku": "WIDGET-001",
      "qty": 2,
      "price": 19.99,
      "created_at": "2025-10-04T10:00:00Z"
    },
    {
      "id": "...",
      "sku": "GADGET-002",
      "qty": 1,
      "price": 49.99,
      "created_at": "2025-10-04T10:00:00Z"
    }
  ],
  "created_at": "2025-10-04T10:00:00Z",
  "updated_at": "2025-10-04T10:00:00Z",
  "metadata": {"source": "web"}
}
```

### Get Order

```bash
curl http://localhost:8001/orders/123e4567-e89b-12d3-a456-426614174000
```

### Update Order Status

```bash
curl -X PATCH http://localhost:8001/orders/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{"status": "placed"}'
```

## NATS Events

### order_created Event

**Subject:** `orders.order_created`

**Payload:**
```json
{
  "event_type": "order_created",
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "total_amount": 89.97,
  "items": [...],
  "created_at": "2025-10-04T10:00:00Z"
}
```

## Health & Metrics

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format - to be implemented)
- **API Docs**: `http://localhost:8001/docs` (Swagger UI)
- **OpenAPI Spec**: `http://localhost:8001/openapi.json`

## Database Schema

Orders Service uses these tables:

- **orders** - Order header (id, customer_id, status, total_amount, timestamps, metadata)
- **order_items** - Order line items (id, order_id, sku, qty, price, created_at)

See `/migrations/001_initial_schema.sql` for full schema.

## Error Handling

- **400 Bad Request** - Invalid input (e.g., empty items array)
- **404 Not Found** - Order not found
- **422 Unprocessable Entity** - Validation errors (Pydantic)
- **500 Internal Server Error** - Database or NATS failures

## Future Enhancements

- [ ] Prometheus metrics with `prometheus_client`
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Rate limiting
- [ ] Idempotency keys
- [ ] Customer validation (check if customer exists)
- [ ] Product/SKU validation (check if SKU exists in inventory)
- [ ] Order cancellation workflow
- [ ] Saga pattern for distributed transactions
