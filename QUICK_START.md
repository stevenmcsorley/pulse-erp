# Pulse ERP - Quick Start Guide

Quick reference for starting the Pulse ERP system on this Raspberry Pi.

## 🚀 Starting the System

### Step 1: Start Base Infrastructure

```bash
cd /home/smcso/erp
docker compose -f docker-compose.base.yml up -d
```

This starts:
- ✅ Traefik (reverse proxy)
- ✅ PostgreSQL (database)
- ✅ NATS JetStream (event bus)
- ✅ MinIO (object storage)
- ✅ Prometheus (metrics)
- ✅ Grafana (dashboards)

### Step 2: Start ERP Services

```bash
docker compose -f docker-compose.base.yml -f docker-compose.services.yml up -d
```

This starts:
- ✅ Orders Service (port 8011)
- ✅ Inventory Service (port 8012)
- ✅ Billing Service (port 8013)
- ✅ OLAP Worker (port 8014)

### Step 3: Start Frontend

```bash
docker compose -f docker-compose.base.yml -f docker-compose.services.yml -f docker-compose.erp.yml up -d
```

This starts:
- ✅ Next.js Frontend (port 3001)

## 🔍 Verify Everything is Running

```bash
# Check all services
docker compose -f docker-compose.base.yml -f docker-compose.services.yml -f docker-compose.erp.yml ps

# Or check with grep
docker ps | grep pulse
```

All services should show `Up` and `(healthy)` status.

## 🌐 Access the Application

### Main Application
```
http://localhost:3001
```

### API Documentation (Swagger)
```
http://localhost:8011/docs  # Orders API
http://localhost:8012/docs  # Inventory API
http://localhost:8013/docs  # Billing API
http://localhost:8014/docs  # OLAP API
```

### Dashboards & Monitoring
```
http://localhost:3010       # Grafana (admin/admin123)
http://localhost:8090       # Traefik Dashboard
http://localhost:9090       # Prometheus
http://localhost:9011       # MinIO Console
```

## 📊 Load Demo Data

```bash
./scripts/seed_demo.sh
```

This creates:
- 3 customers
- 5 products with stock
- 10 sample orders

## 🧪 Run E2E Tests

```bash
cd e2e
npm install
npx playwright install --with-deps chromium
npm test
```

## 🛑 Stop the System

### Stop all services
```bash
docker compose -f docker-compose.base.yml -f docker-compose.services.yml -f docker-compose.erp.yml down
```

### Stop and remove volumes (⚠️ deletes all data)
```bash
docker compose -f docker-compose.base.yml -f docker-compose.services.yml -f docker-compose.erp.yml down -v
```

## 🔧 Troubleshooting

### View logs for a specific service
```bash
docker logs -f pulse-orders     # Orders service
docker logs -f pulse-frontend   # Frontend
docker logs -f pulse-grafana    # Grafana
```

### Restart a single service
```bash
docker compose -f docker-compose.base.yml restart grafana
```

### Check service health
```bash
curl http://localhost:8011/health  # Orders
curl http://localhost:3010/api/health  # Grafana
```

### Rebuild a service after code changes
```bash
docker compose -f docker-compose.base.yml -f docker-compose.services.yml build orders
docker compose -f docker-compose.base.yml -f docker-compose.services.yml up -d orders
```

## 📁 Important Files

- `docker-compose.base.yml` - Infrastructure services
- `docker-compose.services.yml` - Backend microservices
- `docker-compose.erp.yml` - Frontend application
- `.env` - Environment configuration
- `nats.conf` - NATS JetStream configuration
- `PORT_MAPPINGS.md` - Port assignments (avoid conflicts)

## 🎯 Demo Flow

See `demo/DEMO_SCRIPT.md` for the full 7-minute demo walkthrough.

Quick demo:
1. Create product → http://localhost:3001/inventory/products/new
2. Set stock level → Use quick actions (+50 twice = 100 units)
3. Create order → http://localhost:3001/orders/new
4. Place order → Click "Place Order" button
5. View invoice → http://localhost:3001/invoices
6. Mark paid → Click "Mark as Paid"
7. View dashboards → http://localhost:3001/dashboards

## ⚡ One-Line Start (All Services)

```bash
docker compose -f docker-compose.base.yml -f docker-compose.services.yml -f docker-compose.erp.yml up -d && docker compose -f docker-compose.base.yml -f docker-compose.services.yml -f docker-compose.erp.yml ps
```

---

**Need Help?** Check `DEPLOYMENT.md` for detailed deployment guide and troubleshooting.
