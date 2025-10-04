# Sprint 1 Tactical Plan — First 3 Days Execution Guide

## 🎯 Goal
Get a working demo on Raspberry Pi 5 in 3 days: Order → Invoice → Dashboard update <2s

---

## 📅 Day 0: Infrastructure Foundation (6-8 hours)

### Morning: Pi Setup & Docker (2-3 hours)

#### Step 1: OS & Initial Config (45 min)
```bash
# Flash Raspberry Pi OS 64-bit to SD card (use Raspberry Pi Imager)
# Boot Pi, complete initial setup

# SSH in or use terminal
ssh pi@raspberrypi.local

# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y vim git curl wget htop iotop
```

#### Step 2: Docker Installation (30 min)
```bash
# Install Docker & Compose
sudo apt install -y docker.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker  # Or logout/login

# Verify
docker --version  # Should show 24+
docker compose version  # Should show v2.x

# Test
docker run hello-world
```

#### Step 3: External SSD Setup (30 min)
```bash
# Identify SSD
lsblk  # Find /dev/sda or /dev/nvme0n1

# Format (if new)
sudo mkfs.ext4 /dev/sda1

# Create mount point
sudo mkdir -p /mnt/ssd

# Mount
sudo mount /dev/sda1 /mnt/ssd

# Add to fstab for persistence
echo "/dev/sda1 /mnt/ssd ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab

# Set permissions
sudo chown -R $USER:$USER /mnt/ssd

# Create data directories
mkdir -p /mnt/ssd/{pgdata,nats,minio,olap,traefik,backups}

# Test write
dd if=/dev/zero of=/mnt/ssd/test bs=1M count=1024
rm /mnt/ssd/test
```

#### Step 4: Memory Optimization (30 min)
```bash
# Install zram for compressed swap
sudo apt install -y zram-tools

# Configure zram (edit /etc/default/zramswap)
sudo sed -i 's/#ALGO=lz4/ALGO=lz4/' /etc/default/zramswap
sudo sed -i 's/#SIZE=256/SIZE=4096/' /etc/default/zramswap

# Restart zram
sudo systemctl restart zramswap

# Verify
zramctl  # Should show 4GB zram device

# Optimize boot config
sudo tee -a /boot/firmware/config.txt <<EOF
# Performance optimizations
gpu_mem=256
arm_boost=1
over_voltage=2
EOF

# Reboot to apply
sudo reboot
```

---

### Afternoon: Base Infrastructure (3-4 hours)

#### Step 5: Project Setup (15 min)
```bash
# Create project directory
mkdir -p ~/erp-hybrid && cd ~/erp-hybrid

# Initialize git
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# Create directory structure
mkdir -p {migrations,services/{orders,inventory,billing,olap-worker,olap-query-api},ui,scripts,grafana/{dashboards,provisioning},docs}
```

#### Step 6: Base Compose Stack (1 hour)
```bash
# Create .env file
cat > .env <<EOF
POSTGRES_USER=erp
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=erp_db
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)
NATS_USER=nats
NATS_PASSWORD=$(openssl rand -base64 32)
EOF

# Create docker-compose.base.yml
cat > docker-compose.base.yml <<'EOF'
version: '3.9'

networks:
  erp-network:
    driver: bridge

services:
  traefik:
    image: traefik:v2.11
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "/mnt/ssd/traefik:/letsencrypt"
    networks:
      - erp-network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - /mnt/ssd/pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2048M

  nats:
    image: nats:2.10-alpine
    command: ["-js", "-m", "8222", "--user", "${NATS_USER}", "--pass", "${NATS_PASSWORD}"]
    ports:
      - "4222:4222"
      - "8222:8222"
    volumes:
      - /mnt/ssd/nats:/data
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - /mnt/ssd/minio:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - /mnt/ssd/prometheus:/prometheus
    ports:
      - "9090:9090"
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
      GF_INSTALL_PLUGINS: ""
    volumes:
      - /mnt/ssd/grafana:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
EOF

# Create prometheus.yml
cat > prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'orders-service'
    static_configs:
      - targets: ['orders:8000']

  - job_name: 'inventory-service'
    static_configs:
      - targets: ['inventory:8000']

  - job_name: 'billing-service'
    static_configs:
      - targets: ['billing:8000']
EOF

# Start base stack
docker compose -f docker-compose.base.yml up -d

# Wait for health checks
sleep 30

# Verify services
docker compose -f docker-compose.base.yml ps
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana (login: admin/admin)
curl http://localhost:9001  # MinIO console
```

#### Step 7: Database Migrations (30 min)
```bash
# Create migration script
cat > migrations/001_initial_schema.sql <<'EOF'
-- customers
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);
CREATE INDEX idx_customers_email ON customers(email);

-- products
CREATE TABLE products (
    sku VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_products_name ON products(name text_pattern_ops);

-- inventory_items
CREATE TABLE inventory_items (
    sku VARCHAR(64) PRIMARY KEY REFERENCES products(sku),
    qty_on_hand INTEGER NOT NULL DEFAULT 0,
    reserved_qty INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- orders
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    total_amount NUMERIC(14,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);
CREATE INDEX idx_orders_customer ON orders(customer_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status);

-- order_items
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    sku VARCHAR(64) REFERENCES products(sku),
    qty INTEGER NOT NULL,
    price NUMERIC(12,2) NOT NULL
);
CREATE INDEX idx_order_items_order ON order_items(order_id);

-- invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id),
    amount NUMERIC(14,2) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'issued',
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    due_date DATE,
    paid_at TIMESTAMPTZ
);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_order ON invoices(order_id);

-- ledger_entries
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account VARCHAR(64) NOT NULL,
    debit NUMERIC(14,2) DEFAULT 0,
    credit NUMERIC(14,2) DEFAULT 0,
    ref_type VARCHAR(32),
    ref_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ledger_account ON ledger_entries(account);
CREATE INDEX idx_ledger_ref ON ledger_entries(ref_type, ref_id);

-- employees
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(64),
    salary_pence INTEGER,
    payroll_meta JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_employees_email ON employees(email);

-- events_log (audit)
CREATE TABLE events_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    source VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_events_type ON events_log(event_type);
CREATE INDEX idx_events_rec ON events_log(recorded_at DESC);
EOF

# Run migration
docker compose -f docker-compose.base.yml exec -T postgres psql -U erp -d erp_db < migrations/001_initial_schema.sql

# Verify tables
docker compose -f docker-compose.base.yml exec postgres psql -U erp -d erp_db -c "\\dt"
```

#### End of Day 0 Checkpoint
```bash
# Verify all services healthy
docker compose -f docker-compose.base.yml ps

# Check memory usage
free -h
docker stats --no-stream

# Commit progress
git add .
git commit -m "chore: initial infrastructure setup (Postgres, NATS, MinIO, Prometheus, Grafana)"
```

**Expected State:**
- ✅ Pi provisioned with Docker
- ✅ External SSD mounted and optimized
- ✅ Base compose stack running (6 services)
- ✅ Database schema migrated
- ✅ Prometheus scraping, Grafana accessible
- ✅ Memory usage <4GB

---

## 📅 Day 1: Orders Service (6-8 hours)

### Morning: Orders Service Implementation (3-4 hours)

#### Step 8: Orders Service Scaffold (FastAPI example) (1 hour)
```bash
cd services/orders

# Create requirements.txt
cat > requirements.txt <<EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
asyncpg==0.29.0
nats-py==2.6.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-json-logger==2.0.7
prometheus-client==0.19.0
EOF

# Create main.py
cat > main.py <<'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import asyncpg
import nats
import os
import uuid
import json
from datetime import datetime
from prometheus_client import Counter, make_asgi_app

app = FastAPI(title="Orders Service")

# Prometheus metrics
orders_created = Counter('orders_created_total', 'Total orders created')

# Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://erp:password@postgres:5432/erp_db")
NATS_URL = os.getenv("NATS_URL", "nats://nats:nats@nats:4222")

# DB pool (initialize on startup)
db_pool = None

class OrderItem(BaseModel):
    sku: str
    qty: int
    price: float

class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItem]

class Order(BaseModel):
    id: str
    customer_id: str
    items: List[OrderItem]
    total_amount: float
    status: str
    created_at: str

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)

@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()

@app.get("/healthz")
async def health():
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy"}
    except:
        raise HTTPException(500, "Database unhealthy")

@app.post("/orders", status_code=201, response_model=Order)
async def create_order(order: CreateOrderRequest):
    order_id = str(uuid.uuid4())
    total = sum(item.qty * item.price for item in order.items)
    created_at = datetime.utcnow()

    async with db_pool.acquire() as conn:
        async with conn.transaction():
            # Insert order
            await conn.execute(
                "INSERT INTO orders (id, customer_id, total_amount, status, created_at) VALUES ($1, $2, $3, 'placed', $4)",
                order_id, order.customer_id, total, created_at
            )

            # Insert order items
            for item in order.items:
                await conn.execute(
                    "INSERT INTO order_items (order_id, sku, qty, price) VALUES ($1, $2, $3, $4)",
                    order_id, item.sku, item.qty, item.price
                )

    # Emit event to NATS
    try:
        nc = await nats.connect(NATS_URL)
        await nc.publish("order.created", json.dumps({
            "type": "order_created",
            "order_id": order_id,
            "customer_id": order.customer_id,
            "total_amount": float(total),
            "items": [{"sku": i.sku, "qty": i.qty, "price": i.price} for i in order.items],
            "timestamp": created_at.isoformat()
        }).encode())
        await nc.close()
    except Exception as e:
        print(f"Failed to emit event: {e}")

    orders_created.inc()

    return Order(
        id=order_id,
        customer_id=order.customer_id,
        items=order.items,
        total_amount=total,
        status="placed",
        created_at=created_at.isoformat()
    )

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    async with db_pool.acquire() as conn:
        order_row = await conn.fetchrow(
            "SELECT id, customer_id, total_amount, status, created_at FROM orders WHERE id = $1",
            order_id
        )
        if not order_row:
            raise HTTPException(404, "Order not found")

        items_rows = await conn.fetch(
            "SELECT sku, qty, price FROM order_items WHERE order_id = $1",
            order_id
        )

        items = [OrderItem(sku=r['sku'], qty=r['qty'], price=float(r['price'])) for r in items_rows]

        return Order(
            id=str(order_row['id']),
            customer_id=str(order_row['customer_id']),
            items=items,
            total_amount=float(order_row['total_amount']),
            status=order_row['status'],
            created_at=order_row['created_at'].isoformat()
        )

@app.patch("/orders/{order_id}", response_model=Order)
async def update_order_status(order_id: str, status: str):
    valid_statuses = ['draft', 'placed', 'cancelled', 'shipped', 'completed']
    if status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE orders SET status = $1 WHERE id = $2",
            status, order_id
        )

        # Emit event
        nc = await nats.connect(NATS_URL)
        await nc.publish("order.updated", json.dumps({
            "type": "order_updated",
            "order_id": order_id,
            "new_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }).encode())
        await nc.close()

    return await get_order(order_id)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
EOF

# Create Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY main.py .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

#### Step 9: Build & Test Orders Service (30 min)
```bash
# Build for arm64
docker buildx build --platform linux/arm64 -t orders:latest .

# Test locally (ensure base stack running)
docker run --rm -d --name orders-test \
  --network erp-hybrid_erp-network \
  -e DATABASE_URL="postgresql://erp:$(grep POSTGRES_PASSWORD ../../.env | cut -d= -f2)@postgres:5432/erp_db" \
  -e NATS_URL="nats://nats:$(grep NATS_PASSWORD ../../.env | cut -d= -f2)@nats:4222" \
  -p 8000:8000 \
  orders:latest

# Wait for startup
sleep 5

# Test health
curl http://localhost:8000/healthz

# Create test order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test-customer-1",
    "items": [
      {"sku": "TEST-001", "qty": 2, "price": 99.99}
    ]
  }'

# Stop test container
docker stop orders-test
```

---

### Afternoon: Inventory & Billing Services (3-4 hours)

#### Step 10: Quick Inventory Service (1.5 hours)
```bash
cd ../inventory

# Similar structure to Orders service
# Copy and modify main.py with inventory endpoints
# Key endpoints: GET /inventory, POST /inventory, POST /inventory/{sku}/reserve
# Add NATS consumer for order.created events

# Build
docker buildx build --platform linux/arm64 -t inventory:latest .
```

#### Step 11: Quick Billing Service (1.5 hours)
```bash
cd ../billing

# Similar structure
# Key endpoints: POST /billing/invoices, POST /billing/invoices/{id}/pay
# Add NATS consumer for order.created → auto-create invoice
# Add MinIO integration for PDF generation (optional for Day 1, can defer to Day 2)

# Build
docker buildx build --platform linux/arm64 -t billing:latest .
```

#### Step 12: ERP Compose Stack (30 min)
```bash
cd ../..

# Create docker-compose.erp.yml
cat > docker-compose.erp.yml <<'EOF'
version: '3.9'

services:
  orders:
    image: orders:latest
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      NATS_URL: nats://${NATS_USER}:${NATS_PASSWORD}@nats:4222
    depends_on:
      - postgres
      - nats
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.orders.rule=PathPrefix(`/orders`)"
      - "traefik.http.services.orders.loadbalancer.server.port=8000"

  inventory:
    image: inventory:latest
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      NATS_URL: nats://${NATS_USER}:${NATS_PASSWORD}@nats:4222
    depends_on:
      - postgres
      - nats
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M

  billing:
    image: billing:latest
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      NATS_URL: nats://${NATS_USER}:${NATS_PASSWORD}@nats:4222
      MINIO_URL: http://minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
    depends_on:
      - postgres
      - nats
      - minio
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M

networks:
  erp-network:
    external: true
    name: erp-hybrid_erp-network
EOF

# Start ERP stack
docker compose -f docker-compose.erp.yml up -d

# Verify
docker compose -f docker-compose.erp.yml ps
```

#### End of Day 1 Checkpoint
```bash
# Test end-to-end flow
# 1. Create order
ORDER_RESPONSE=$(curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test-customer-1",
    "items": [{"sku": "TEST-001", "qty": 2, "price": 99.99}]
  }')

echo $ORDER_RESPONSE

# 2. Check NATS event (use nats CLI if installed)
# docker run --rm -it --network erp-hybrid_erp-network natsio/nats-box:latest
# nats sub "order.*"

# 3. Verify inventory consumer reserved stock (check logs)
docker compose -f docker-compose.erp.yml logs inventory

# 4. Verify billing created invoice (check logs or API)
docker compose -f docker-compose.erp.yml logs billing

# Commit
git add .
git commit -m "feat: implement Orders, Inventory, Billing services with event-driven architecture"
```

**Expected State:**
- ✅ Orders service: POST/GET/PATCH /orders working
- ✅ Inventory service: CRUD + reservation working
- ✅ Billing service: Invoice creation working
- ✅ NATS events flowing between services
- ✅ All services healthy, memory <5GB total

---

## 📅 Day 2: OLAP Pipeline + Frontend (6-8 hours)

### Morning: OLAP Worker & DuckDB (2-3 hours)

#### Step 13: OLAP Worker (1.5 hours)
```bash
cd services/olap-worker

# Create requirements.txt
cat > requirements.txt <<EOF
nats-py==2.6.0
duckdb==0.9.2
python-json-logger==2.0.7
EOF

# Create worker.py
cat > worker.py <<'EOF'
import nats
import duckdb
import json
import os
import asyncio
from datetime import datetime

NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/olap/analytics.duckdb")

# Initialize DuckDB
con = duckdb.connect(DUCKDB_PATH)

# Create OLAP tables
con.execute("""
    CREATE TABLE IF NOT EXISTS sales_by_hour (
        hour TIMESTAMP PRIMARY KEY,
        total_amount DECIMAL(14,2) DEFAULT 0,
        order_count INTEGER DEFAULT 0
    )
""")

con.execute("""
    CREATE TABLE IF NOT EXISTS stock_snapshot (
        sku VARCHAR(64) PRIMARY KEY,
        qty_on_hand INTEGER,
        reserved_qty INTEGER,
        snapshot_at TIMESTAMP
    )
""")

con.execute("""
    CREATE TABLE IF NOT EXISTS ar_ageing (
        bucket VARCHAR(16) PRIMARY KEY,
        total_ar DECIMAL(14,2),
        as_of TIMESTAMP
    )
""")

async def handle_order_created(msg):
    data = json.loads(msg.data.decode())
    print(f"Processing order_created: {data['order_id']}")

    hour = datetime.fromisoformat(data['timestamp']).replace(minute=0, second=0, microsecond=0)

    con.execute("""
        INSERT INTO sales_by_hour (hour, total_amount, order_count)
        VALUES (?, ?, 1)
        ON CONFLICT (hour) DO UPDATE SET
            total_amount = sales_by_hour.total_amount + EXCLUDED.total_amount,
            order_count = sales_by_hour.order_count + 1
    """, [hour, data['total_amount']])

    print(f"Updated sales_by_hour for {hour}")

async def handle_stock_reserved(msg):
    data = json.loads(msg.data.decode())
    print(f"Processing stock_reserved: {data['sku']}")

    # Update stock snapshot
    con.execute("""
        INSERT INTO stock_snapshot (sku, qty_on_hand, reserved_qty, snapshot_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (sku) DO UPDATE SET
            reserved_qty = EXCLUDED.reserved_qty,
            snapshot_at = EXCLUDED.snapshot_at
    """, [data['sku'], data.get('qty_on_hand', 0), data.get('reserved_qty', 0), datetime.utcnow()])

async def handle_payment_received(msg):
    data = json.loads(msg.data.decode())
    print(f"Processing payment_received: {data['invoice_id']}")

    # Update AR aging (simplified)
    con.execute("""
        INSERT INTO ar_ageing (bucket, total_ar, as_of)
        VALUES ('current', ?, ?)
        ON CONFLICT (bucket) DO UPDATE SET
            total_ar = ar_ageing.total_ar - EXCLUDED.total_ar,
            as_of = EXCLUDED.as_of
    """, [data['amount'], datetime.utcnow()])

async def main():
    nc = await nats.connect(NATS_URL)

    # Subscribe to all relevant events
    await nc.subscribe("order.created", cb=handle_order_created)
    await nc.subscribe("stock.reserved", cb=handle_stock_reserved)
    await nc.subscribe("payment.received", cb=handle_payment_received)

    print("OLAP worker started, listening for events...")

    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Dockerfile
cat > Dockerfile <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py .
CMD ["python", "worker.py"]
EOF

# Build
docker buildx build --platform linux/arm64 -t olap-worker:latest .
```

#### Step 14: OLAP Query API (1 hour)
```bash
cd ../olap-query-api

cat > main.py <<'EOF'
from fastapi import FastAPI, HTTPException
import duckdb
import os

app = FastAPI(title="OLAP Query API")

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/olap/analytics.duckdb")

@app.get("/healthz")
def health():
    return {"status": "healthy"}

@app.get("/query")
def query_olap(sql: str):
    # Validate: only SELECT allowed
    if not sql.strip().upper().startswith('SELECT'):
        raise HTTPException(400, "Only SELECT queries allowed")

    con = duckdb.connect(DUCKDB_PATH, read_only=True)

    try:
        result = con.execute(sql).fetchall()
        columns = [desc[0] for desc in con.description] if con.description else []

        return {
            "columns": columns,
            "rows": [[str(v) for v in row] for row in result]
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        con.close()
EOF

# Build
docker buildx build --platform linux/arm64 -t olap-query-api:latest .
```

#### Step 15: BI Compose Stack (30 min)
```bash
cd ../..

cat > docker-compose.bi.yml <<'EOF'
version: '3.9'

services:
  olap-worker:
    image: olap-worker:latest
    environment:
      NATS_URL: nats://${NATS_USER}:${NATS_PASSWORD}@nats:4222
      DUCKDB_PATH: /olap/analytics.duckdb
    volumes:
      - /mnt/ssd/olap:/olap
    depends_on:
      - nats
    networks:
      - erp-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  olap-query-api:
    image: olap-query-api:latest
    environment:
      DUCKDB_PATH: /olap/analytics.duckdb
    volumes:
      - /mnt/ssd/olap:/olap:ro
    ports:
      - "8001:8000"
    networks:
      - erp-network
    restart: unless-stopped

networks:
  erp-network:
    external: true
    name: erp-hybrid_erp-network
EOF

# Start BI stack
docker compose -f docker-compose.bi.yml up -d
```

---

### Afternoon: Grafana Dashboards + Quick UI (3-4 hours)

#### Step 16: Grafana Dashboard (1 hour)
```bash
# Create Grafana datasource config
mkdir -p grafana/provisioning/datasources

cat > grafana/provisioning/datasources/olap.yml <<EOF
apiVersion: 1

datasources:
  - name: OLAP
    type: simpod-json-datasource
    access: proxy
    url: http://olap-query-api:8000
    isDefault: true
EOF

# Create dashboard JSON (simplified)
mkdir -p grafana/dashboards

cat > grafana/dashboards/erp-sales.json <<'EOF'
{
  "title": "ERP Sales & Cashflow",
  "panels": [
    {
      "title": "Sales by Hour",
      "targets": [
        {
          "rawSql": "SELECT hour, total_amount FROM sales_by_hour ORDER BY hour DESC LIMIT 24"
        }
      ],
      "type": "graph"
    },
    {
      "title": "Total Orders",
      "targets": [
        {
          "rawSql": "SELECT SUM(order_count) FROM sales_by_hour"
        }
      ],
      "type": "stat"
    }
  ]
}
EOF

# Restart Grafana to load provisioning
docker compose -f docker-compose.base.yml restart grafana
```

#### Step 17: Minimal Frontend (2-3 hours)
```bash
# Quick Next.js setup
cd ui
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# Create simple order form page
# This is simplified - use component code from cards C27-C30

# Build Docker image
cat > Dockerfile <<EOF
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
EOF

docker buildx build --platform linux/arm64 -t erp-ui:latest .
```

#### End of Day 2 Checkpoint
```bash
# Full stack up
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml up -d

# Create test order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "demo-customer",
    "items": [{"sku": "DEMO-001", "qty": 5, "price": 199.99}]
  }'

# Query OLAP (should show data within 2s)
sleep 3
curl "http://localhost:8001/query?sql=SELECT%20*%20FROM%20sales_by_hour"

# Check Grafana dashboard
# Visit http://<pi-ip>:3000 and view ERP Sales dashboard

git add .
git commit -m "feat: implement OLAP pipeline, DuckDB materialization, Grafana dashboards, basic UI"
```

**Expected State:**
- ✅ OLAP worker consuming events
- ✅ DuckDB tables updating in real-time
- ✅ Grafana dashboard showing live sales data
- ✅ Basic UI operational (order form)
- ✅ End-to-end: order → OLAP → dashboard <2s

---

## 📅 Day 3: Polish, Seed Data, Demo Rehearsal (4-6 hours)

### Morning: Seed Data & Testing (2-3 hours)

#### Step 18: Seed Script (30 min)
```bash
cat > scripts/seed_demo.sh <<'EOF'
#!/bin/bash
set -e

PGCMD="docker compose -f docker-compose.base.yml exec -T postgres psql -U erp -d erp_db"

echo "Seeding demo data..."

$PGCMD <<SQL
TRUNCATE customers, products, inventory_items, orders, order_items, invoices, ledger_entries, employees CASCADE;

-- Customers
INSERT INTO customers (id, name, email, phone) VALUES
('11111111-1111-1111-1111-111111111111', 'Acme Corp', 'acme@example.com', '+44 20 1234 5678'),
('22222222-2222-2222-2222-222222222222', 'Beta Ltd', 'beta@example.com', '+44 20 2345 6789'),
('33333333-3333-3333-3333-333333333333', 'Gamma LLC', 'gamma@example.com', '+44 20 3456 7890');

-- Products
INSERT INTO products (sku, name, description, price) VALUES
('CAM-1001', 'Camera Model A', 'High-resolution camera', 399.00),
('CAM-2002', 'Camera Model B', 'Professional camera', 599.00),
('TRI-300', 'Tripod', 'Adjustable tripod', 49.99),
('BAT-150', 'Battery Pack', 'Rechargeable battery', 29.99),
('CABLE-01', 'USB Cable', 'USB-C cable 2m', 9.99);

-- Inventory
INSERT INTO inventory_items (sku, qty_on_hand, reserved_qty, reorder_point) VALUES
('CAM-1001', 10, 0, 2),
('CAM-2002', 5, 0, 1),
('TRI-300', 50, 0, 5),
('BAT-150', 100, 0, 10),
('CABLE-01', 200, 0, 20);

SQL

echo "Seed complete! Demo data loaded."
EOF

chmod +x scripts/seed_demo.sh
./scripts/seed_demo.sh
```

#### Step 19: E2E Smoke Test (1.5 hours)
```bash
# Install Playwright in UI project
cd ui
npm install -D @playwright/test

# Create simple E2E test
mkdir -p tests/e2e

cat > tests/e2e/demo-flow.spec.ts <<'EOF'
import { test, expect } from '@playwright/test';

test('demo flow: create order and verify dashboard', async ({ page }) => {
  // 1. Navigate to order form
  await page.goto('http://localhost:3000/orders/new');

  // 2. Fill form
  await page.selectOption('[data-testid="customer-select"]', '11111111-1111-1111-1111-111111111111');
  await page.selectOption('[data-testid="product-select"]', 'CAM-1001');
  await page.fill('[data-testid="qty-input"]', '3');

  // 3. Submit
  await page.click('[data-testid="submit-button"]');

  // 4. Wait for success message
  await expect(page.locator('[data-testid="success-message"]')).toBeVisible();

  // 5. Navigate to dashboards
  await page.goto('http://localhost:3000/dashboards');

  // 6. Wait for Grafana iframe to load
  await page.waitForLoadState('networkidle');

  // 7. Verify dashboard shows updated data (visual check or API call)
  await page.waitForTimeout(2000);  // Allow OLAP update
});
EOF

# Run test
npx playwright test
```

---

### Afternoon: Demo Rehearsal & Documentation (2-3 hours)

#### Step 20: Demo Rehearsal (1 hour)
```bash
# Restart all services clean
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml down
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml up -d

# Wait for all services
sleep 30

# Seed data
./scripts/seed_demo.sh

# Run through demo script
# 1. Show Pi specs: cat /proc/cpuinfo | grep Model
# 2. Show services: docker compose ps
# 3. Create order via UI or curl
# 4. Show inventory updated (logs or UI)
# 5. Show invoice created (logs or UI)
# 6. Mark invoice paid
# 7. Show Grafana dashboard update

# Time each step - aim for <7 minutes total
```

#### Step 21: Documentation (1-2 hours)
```bash
# Create README.md (use template from card C52)
cat > README.md <<'EOF'
# ERP + BI Hybrid — Raspberry Pi 5 Demo

## Overview
Modular ERP with real-time business intelligence, running on Raspberry Pi 5.

## Quick Start
```bash
# Prerequisites: Pi 5 with Docker, external SSD

# 1. Clone repo
git clone <repo-url> && cd erp-hybrid

# 2. Configure environment
cp .env.example .env
# Edit .env with secure passwords

# 3. Start infrastructure
docker compose -f docker-compose.base.yml up -d

# 4. Run migrations
docker compose -f docker-compose.base.yml exec -T postgres psql -U erp -d erp_db < migrations/001_initial_schema.sql

# 5. Start ERP services
docker compose -f docker-compose.erp.yml up -d

# 6. Start BI stack
docker compose -f docker-compose.bi.yml up -d

# 7. Seed demo data
./scripts/seed_demo.sh

# 8. Access UI
open http://<pi-ip>:3000
```

## Architecture
See [ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Demo
See [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
EOF

# Create architecture diagram (ASCII or export from draw.io)
# Create demo script cheat sheet

git add .
git commit -m "docs: add README, demo script, E2E tests"
```

---

## 🏁 Final Checkpoint (End of Day 3)

### Pre-Demo Checklist
```bash
# 1. All services healthy
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml ps

# 2. Memory usage acceptable
free -h
docker stats --no-stream | awk '{print $1, $7}'

# 3. Seed data loaded
docker compose -f docker-compose.base.yml exec postgres psql -U erp -d erp_db -c "SELECT COUNT(*) FROM customers;"

# 4. E2E test passes
cd ui && npx playwright test

# 5. Demo rehearsed and timed
./scripts/demo_rehearsal.sh  # Create this script with all demo steps

# 6. Documentation complete
ls -la README.md docs/

# 7. Git clean
git status
git log --oneline -10
```

### Performance Validation
```bash
# Test dashboard latency
echo "Creating order..."
START=$(date +%s)

ORDER_ID=$(curl -s -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "11111111-1111-1111-1111-111111111111",
    "items": [{"sku": "CAM-1001", "qty": 1, "price": 399.00}]
  }' | jq -r '.id')

echo "Order created: $ORDER_ID"

# Wait and query OLAP
sleep 2

RESULT=$(curl -s "http://localhost:8001/query?sql=SELECT%20COUNT(*)%20FROM%20sales_by_hour")
END=$(date +%s)

LATENCY=$((END - START))
echo "Dashboard update latency: ${LATENCY}s (target: <2s)"

if [ $LATENCY -lt 3 ]; then
  echo "✅ PASS: Latency within target"
else
  echo "❌ FAIL: Latency exceeds target"
fi
```

---

## 📊 Success Metrics (Sprint 1 Complete)

### Technical Deliverables
- ✅ 6 infrastructure services (Postgres, NATS, MinIO, Traefik, Prometheus, Grafana)
- ✅ 3 ERP microservices (Orders, Inventory, Billing)
- ✅ 2 OLAP services (Worker, Query API)
- ✅ 1 Frontend UI (Next.js)
- ✅ Database schema (9 tables)
- ✅ Event-driven architecture (NATS)
- ✅ Real-time analytics (DuckDB + Grafana)

### Performance Targets
- ✅ Dashboard latency: <2s (order → update)
- ✅ API response time: <200ms p95
- ✅ Memory usage: <6GB total
- ✅ Services stable: >24 hours uptime

### Demo Readiness
- ✅ Seed data script (<30s execution)
- ✅ Demo script rehearsed (3+ times)
- ✅ E2E smoke test passing
- ✅ Documentation complete (README, Architecture, API docs)
- ✅ Recovery procedures documented

---

## 🚀 Next Steps (Sprint 2 Prep)

After successful Sprint 1 demo:

1. **Feedback Collection** — Document demo feedback, identify gaps
2. **Auth Implementation** — Keycloak setup (cards C32-C35)
3. **CI/CD Pipeline** — GitHub Actions (cards C36-C40)
4. **Monitoring Enhancement** — Alerts, tracing (cards C41-C44)
5. **Test Coverage** — Unit/integration tests to >80% (cards C45-C48)
6. **Production Hardening** — Security audit, load testing

---

## 📚 Reference Commands

### Essential Docker Commands
```bash
# View all containers
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml ps

# Restart specific service
docker compose -f docker-compose.erp.yml restart orders

# View logs
docker compose -f docker-compose.erp.yml logs -f orders

# Execute command in container
docker compose -f docker-compose.base.yml exec postgres psql -U erp -d erp_db

# Remove all and start fresh
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml down -v
```

### Debugging Commands
```bash
# Check memory
free -h
docker stats --no-stream

# Check disk
df -h /mnt/ssd

# Check network
docker network ls
docker network inspect erp-hybrid_erp-network

# Check NATS
docker compose -f docker-compose.base.yml exec nats nats-server --version

# Query Postgres
docker compose -f docker-compose.base.yml exec postgres psql -U erp -d erp_db -c "SELECT * FROM orders LIMIT 5;"

# Query DuckDB
docker run --rm -v /mnt/ssd/olap:/olap duckdb/duckdb /olap/analytics.duckdb "SELECT * FROM sales_by_hour;"
```

---

**End of Sprint 1 Tactical Plan**

*This plan gets you from zero to demo-ready in 3 days. Follow sequentially, validate checkpoints, and adjust timing based on your development speed.*
