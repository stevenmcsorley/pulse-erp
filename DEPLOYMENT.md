# Pulse ERP - Deployment Guide

Complete deployment instructions for the Pulse ERP system on Raspberry Pi 5.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Traefik                              │
│                  (HTTPS Termination & Routing)               │
└───────┬─────────────────────────────────┬──────────────────┘
        │                                 │
        │                                 │
┌───────▼──────┐                  ┌───────▼────────────────┐
│   Frontend   │                  │   API Services         │
│   (Next.js)  │                  │   - Orders (8001)      │
│   Port 3001  │                  │   - Inventory (8002)   │
│              │                  │   - Billing (8003)     │
│              │                  │   - OLAP (8004)        │
└──────────────┘                  └────────────────────────┘
        │                                 │
        │                                 │
        ▼                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  - PostgreSQL (OLTP)                                        │
│  - NATS JetStream (Event Bus)                              │
│  - DuckDB (OLAP)                                            │
│  - Grafana (Dashboards)                                     │
│  - Prometheus (Metrics)                                     │
└─────────────────────────────────────────────────────────────┘
```

## Stack Components

### Compose Files (Layered)

1. **docker-compose.base.yml** - Infrastructure
   - PostgreSQL, NATS, MinIO, Traefik, Prometheus, Grafana

2. **docker-compose.services.yml** - Microservices
   - Orders, Inventory, Billing, OLAP Worker

3. **docker-compose.bi.yml** - BI Stack
   - Grafana plugin installation, DuckDB persistence

4. **docker-compose.erp.yml** - Frontend
   - Next.js UI with Traefik routing

## Deployment Options

### Option 1: Full Stack (Recommended for Demo)

Deploy everything including frontend UI:

```bash
docker-compose \
  -f docker-compose.base.yml \
  -f docker-compose.services.yml \
  -f docker-compose.bi.yml \
  -f docker-compose.erp.yml \
  up -d
```

### Option 2: Backend + BI Only

Deploy services and analytics without frontend:

```bash
docker-compose \
  -f docker-compose.base.yml \
  -f docker-compose.services.yml \
  -f docker-compose.bi.yml \
  up -d
```

### Option 3: Infrastructure Only

Deploy only base infrastructure:

```bash
docker-compose -f docker-compose.base.yml up -d
```

## Environment Variables

Create `.env` file in project root:

```bash
# Database
POSTGRES_DB=pulse_erp
POSTGRES_USER=pulseadmin
POSTGRES_PASSWORD=changeme

# Domain (for Traefik routing)
DOMAIN=local

# Data paths
DATA_PATH=./data

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin
GF_AUTH_ANONYMOUS_ENABLED=true
GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
```

## Pre-Deployment Checklist

1. **Create Docker network:**
   ```bash
   docker network create pulse-network
   ```

2. **Create data directories:**
   ```bash
   mkdir -p data/postgres data/duckdb data/minio
   ```

3. **Run database migrations:**
   ```bash
   ./scripts/migrate.sh
   ```

4. **Initialize DuckDB schema:**
   ```bash
   ./scripts/init-duckdb.sh
   ```

## URLs & Access

After deployment, services are accessible at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | https://app.local | Next.js UI |
| API Gateway | https://api.local | All microservices |
| Orders API | https://api.local/orders | Orders endpoints |
| Inventory API | https://api.local/inventory | Inventory endpoints |
| Billing API | https://api.local/billing | Billing endpoints |
| OLAP API | https://api.local/olap | Analytics queries |
| Grafana | https://grafana.local | Dashboards |
| Traefik | https://traefik.local | Traefik dashboard |

**Note:** Add entries to `/etc/hosts` for local development:
```
127.0.0.1 app.local api.local grafana.local traefik.local
```

## Health Checks

Check service health:

```bash
# All services
docker-compose ps

# Specific service
docker exec pulse-frontend node -e "require('http').get('http://localhost:3000/', (r) => {console.log(r.statusCode)})"

# API endpoints
curl http://localhost:8001/health  # Orders
curl http://localhost:8002/health  # Inventory
curl http://localhost:8003/health  # Billing
curl http://localhost:8004/health  # OLAP
```

## Building Images

### Frontend

```bash
cd frontend
docker buildx build \
  --platform linux/arm64 \
  -t registry:5000/frontend:latest \
  --push .
```

### Services

```bash
# Orders
cd services/orders
docker buildx build --platform linux/arm64 -t registry:5000/orders:latest --push .

# Inventory
cd services/inventory
docker buildx build --platform linux/arm64 -t registry:5000/inventory:latest --push .

# Billing
cd services/billing
docker buildx build --platform linux/arm64 -t registry:5000/billing:latest --push .

# OLAP Worker
cd services/olap-worker
docker buildx build --platform linux/arm64 -t registry:5000/olap-worker:latest --push .
```

## Troubleshooting

### Frontend not accessible

1. Check container logs:
   ```bash
   docker logs pulse-frontend
   ```

2. Verify Traefik routing:
   ```bash
   docker logs traefik
   ```

3. Check network connectivity:
   ```bash
   docker exec pulse-frontend ping orders
   ```

### API calls failing from frontend

1. Verify environment variables:
   ```bash
   docker exec pulse-frontend env | grep API
   ```

2. Check API service health:
   ```bash
   curl http://localhost:8001/health
   ```

### Grafana dashboards not loading

1. Verify Grafana is running:
   ```bash
   docker ps | grep grafana
   ```

2. Check frontend can reach Grafana:
   ```bash
   docker exec pulse-frontend ping grafana
   ```

3. Verify anonymous access is enabled:
   ```bash
   docker exec grafana cat /etc/grafana/grafana.ini | grep anonymous
   ```

## Resource Limits

Recommended for Raspberry Pi 5 (8GB):

| Service | Memory Limit | Memory Reservation |
|---------|-------------|-------------------|
| Frontend | 512M | 256M |
| Orders | 512M | 256M |
| Inventory | 512M | 256M |
| Billing | 512M | 256M |
| OLAP Worker | 1G | 512M |
| PostgreSQL | 1G | 512M |
| Grafana | 512M | 256M |

Total: ~4.5GB reserved, ~6GB limit

## Backup & Restore

### Backup

```bash
# PostgreSQL
docker exec postgres pg_dump -U pulseadmin pulse_erp > backup.sql

# DuckDB
cp data/duckdb/pulse_olap.duckdb backup/pulse_olap.duckdb
```

### Restore

```bash
# PostgreSQL
cat backup.sql | docker exec -i postgres psql -U pulseadmin pulse_erp

# DuckDB
cp backup/pulse_olap.duckdb data/duckdb/pulse_olap.duckdb
```

## Monitoring

View metrics:
- Prometheus: http://localhost:9090
- Grafana: https://grafana.local
- Traefik Dashboard: https://traefik.local

## Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker logs -f pulse-frontend

# Last 100 lines
docker logs --tail 100 pulse-orders
```

## Stopping Services

```bash
# Stop all
docker-compose \
  -f docker-compose.base.yml \
  -f docker-compose.services.yml \
  -f docker-compose.bi.yml \
  -f docker-compose.erp.yml \
  down

# Stop and remove volumes (DANGER: data loss)
docker-compose \
  -f docker-compose.base.yml \
  -f docker-compose.services.yml \
  -f docker-compose.bi.yml \
  -f docker-compose.erp.yml \
  down -v
```

## Production Considerations

For production deployment:

1. **Use proper SSL certificates** (not self-signed)
2. **Set strong passwords** in `.env`
3. **Enable Grafana authentication** (disable anonymous)
4. **Configure backup automation**
5. **Set up log rotation**
6. **Monitor disk space** (especially DuckDB)
7. **Configure resource limits** per your hardware
8. **Use secrets management** (Docker Secrets or Vault)
