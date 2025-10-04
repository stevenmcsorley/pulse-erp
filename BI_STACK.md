# Pulse ERP - BI Stack Documentation

## Overview

The Pulse ERP BI (Business Intelligence) Stack provides real-time analytics and dashboards for operational decision-making. Built on DuckDB and Grafana, it offers sub-second query performance on a Raspberry Pi 5.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OLTP Layer (PostgreSQL)                   │
│         Orders, Inventory, Billing Microservices             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ NATS Events
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     BI Stack (OLAP)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  OLAP Worker (Port 8004)                               │ │
│  │  - Consumes NATS events                                │ │
│  │  - Materializes to DuckDB                              │ │
│  │  - Provides Query API                                  │ │
│  └────────────────┬────────────────────────────────────────┘ │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  DuckDB (In-process OLAP database)                     │ │
│  │  - sales_by_hour                                        │ │
│  │  - stock_snapshot                                       │ │
│  │  - ar_aging                                             │ │
│  │  - Raw event tables                                     │ │
│  └────────────────┬────────────────────────────────────────┘ │
│                   │                                          │
│                   │ HTTP Query API                           │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Grafana (Port 3000)                                   │ │
│  │  - 3 Pre-configured Dashboards                         │ │
│  │  - JSON API Datasource                                 │ │
│  │  - Auto-provisioning                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. OLAP Worker

**Service:** `pulse-olap-worker`
**Port:** 8004
**Image:** Custom FastAPI app
**Purpose:** Event consumer and query API

**Responsibilities:**
- Subscribes to NATS JetStream events
- Materializes data to DuckDB aggregate tables
- Provides REST API for analytics queries
- Maintains real-time data freshness (<2s latency)

**Key Features:**
- Idempotent event processing
- Automatic schema initialization
- Health checks and metrics
- CORS enabled for frontend

**Endpoints:**
- `/health` - Health check
- `/stats` - Processing statistics
- `/query/sales/hourly` - Hourly sales
- `/query/inventory/low-stock` - Reorder alerts
- `/query/ar/overdue` - Collections data

See `/services/olap-worker/API.md` for full API documentation.

### 2. DuckDB

**Type:** Embedded OLAP database
**Storage:** `/data/duckdb/pulse_olap.duckdb`
**Size:** ~10-50MB (grows with data)

**Tables:**
- **Aggregates:** sales_by_hour, stock_snapshot, ar_aging
- **Events:** order_events, invoice_events, stock_events

**Performance:**
- Query time: <50ms for aggregates
- Insert rate: 1000+ events/sec
- Memory footprint: ~100MB

See `/services/olap-worker/migrations/README.md` for schema details.

### 3. Grafana

**Service:** `pulse-grafana`
**Port:** 3000
**Image:** grafana/grafana:latest
**Credentials:** admin/admin (change on first login)

**Dashboards:**
1. Sales & Revenue - Order trends and revenue metrics
2. Inventory & Stock - Stock levels and reorder alerts
3. Cashflow & AR - AR aging and collections

**Plugins:**
- `marcusolsson-json-datasource` - JSON API datasource for OLAP queries

See `/grafana/DASHBOARDS.md` for dashboard documentation.

---

## Deployment

### Quick Start

```bash
# 1. Start base infrastructure
docker compose -f docker-compose.base.yml up -d

# 2. Start microservices
docker compose -f docker-compose.services.yml up -d

# 3. Start BI stack
docker compose -f docker-compose.bi.yml up -d

# 4. Verify all services healthy
docker ps
```

### Integrated Start

```bash
# Start all layers together
docker compose \
  -f docker-compose.base.yml \
  -f docker-compose.services.yml \
  -f docker-compose.bi.yml \
  up -d
```

### Stop BI Stack Only

```bash
docker compose -f docker-compose.bi.yml down
```

---

## Configuration

### Environment Variables

```bash
# .env file
DATA_PATH=/mnt/ssd/pulse-erp  # SSD mount point
DUCKDB_PATH=/data/pulse_olap.duckdb  # DuckDB file location
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=changeme
```

### Data Persistence

All BI data persists to `/mnt/ssd/pulse-erp/duckdb/` (configurable via `DATA_PATH`).

**Backup:**
```bash
# Backup DuckDB file
cp /mnt/ssd/pulse-erp/duckdb/pulse_olap.duckdb \
   /backups/pulse_olap_$(date +%Y%m%d).duckdb
```

**Restore:**
```bash
# Stop OLAP worker
docker stop pulse-olap-worker

# Restore backup
cp /backups/pulse_olap_20251004.duckdb \
   /mnt/ssd/pulse-erp/duckdb/pulse_olap.duckdb

# Restart worker
docker start pulse-olap-worker
```

---

## Resource Requirements

### Minimum (Development)
- CPU: 2 cores
- RAM: 2GB
- Disk: 10GB

### Recommended (Production on Pi 5)
- CPU: 4 cores
- RAM: 4GB
- Disk: 20GB SSD

### Actual Usage (Typical Workload)
- OLAP Worker: 256MB RAM
- DuckDB: 100MB RAM, 50MB disk
- Grafana: 200MB RAM

---

## Monitoring

### Health Checks

```bash
# OLAP Worker
curl http://localhost:8004/health

# Grafana
curl http://localhost:3000/api/health
```

### Metrics

OLAP Worker exposes Prometheus-compatible metrics (if configured):

```bash
curl http://localhost:8004/metrics
```

### Logs

```bash
# OLAP Worker logs
docker logs -f pulse-olap-worker

# Grafana logs
docker logs -f pulse-grafana
```

---

## Accessing Dashboards

### Grafana Web UI

1. Open browser: `http://localhost:3000`
2. Login with admin/admin
3. Navigate to **Dashboards** → **Browse** → **ERP Analytics**
4. Select dashboard:
   - Sales & Revenue
   - Inventory & Stock
   - Cashflow & AR

### Dashboard URLs

- Sales: `http://localhost:3000/d/sales-revenue-001`
- Inventory: `http://localhost:3000/d/inventory-stock-001`
- Cashflow: `http://localhost:3000/d/cashflow-ar-001`

### Kiosk Mode (TV Display)

```
http://localhost:3000/d/sales-revenue-001?kiosk
```

---

## Troubleshooting

### Issue: Dashboards show "No data"

**Causes:**
- OLAP Worker not running
- No events published yet
- DuckDB schema not initialized

**Solutions:**
```bash
# 1. Check OLAP Worker is running
docker ps | grep olap-worker

# 2. Check worker logs
docker logs pulse-olap-worker

# 3. Verify DuckDB schema
docker exec -it pulse-olap-worker \
  python -c "from app.duckdb_client import duckdb_client; duckdb_client.connect(); print('OK')"

# 4. Seed some test data (see Demo Preparation)
```

### Issue: Plugin not found (JSON datasource)

**Cause:** Grafana plugin not installed

**Solution:**
```bash
docker exec -it pulse-grafana grafana-cli plugins install marcusolsson-json-datasource
docker restart pulse-grafana
```

### Issue: Slow dashboard refresh

**Causes:**
- Query API slow
- Network latency
- Large dataset

**Solutions:**
```bash
# 1. Check query performance
curl -s "http://localhost:8004/query/sales/hourly?hours=24" | jq '.execution_time_ms'

# 2. Check DuckDB indexes
docker exec -it pulse-olap-worker duckdb /data/pulse_olap.duckdb "PRAGMA show_tables"

# 3. Reduce query scope (fewer hours/days)
```

### Issue: DuckDB file corrupted

**Recovery:**
```bash
# Stop worker
docker stop pulse-olap-worker

# Remove corrupted file
rm /mnt/ssd/pulse-erp/duckdb/pulse_olap.duckdb

# Restart worker (will recreate schema)
docker start pulse-olap-worker

# Check logs
docker logs -f pulse-olap-worker
```

---

## Performance Tuning

### OLAP Worker

**Memory:**
```yaml
# docker-compose.bi.yml
services:
  olap-worker:
    deploy:
      resources:
        limits:
          memory: 1G  # Increase if needed
        reservations:
          memory: 512M
```

**Event Batch Size:**
```python
# services/olap-worker/app/consumers/event_consumer.py
messages = await consumer.fetch(batch=20, timeout=5)  # Increase batch
```

### DuckDB

**Indexes:**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_sales_hour ON sales_by_hour(hour);
CREATE INDEX IF NOT EXISTS idx_sku ON stock_snapshot(sku);
```

**Vacuum:**
```bash
# Compact DuckDB file periodically
docker exec -it pulse-olap-worker duckdb /data/pulse_olap.duckdb "VACUUM"
```

### Grafana

**Caching:**
```yaml
# grafana/provisioning/datasources.yml
datasources:
  - name: OLAP Analytics
    jsonData:
      cacheDurationSeconds: 30  # Cache queries for 30s
```

**Refresh Rate:**
```json
// Dashboards: Reduce refresh frequency
{
  "refresh": "10s"  // Change from 5s to 10s
}
```

---

## Scaling Considerations

### Horizontal Scaling

OLAP Worker can be scaled horizontally:

```yaml
# docker-compose.bi.yml
services:
  olap-worker:
    deploy:
      replicas: 3  # Multiple workers
```

**Note:** NATS consumers use work-sharing, so multiple workers will distribute load.

### Vertical Scaling

For larger datasets (1M+ events):
- Increase memory limits
- Use SSD for DuckDB
- Add more indexes
- Consider DuckDB partitioning

---

## Security

### Current (Development)

- No authentication on OLAP API
- Grafana: Basic auth (admin/admin)
- CORS: Allow all origins

### Production Recommendations

- [ ] Add JWT authentication to OLAP API
- [ ] Use Keycloak for Grafana SSO
- [ ] Restrict CORS origins
- [ ] Enable HTTPS (Traefik)
- [ ] Use secrets for passwords

---

## Maintenance

### Daily
- Monitor dashboard performance
- Check error logs

### Weekly
- Backup DuckDB file
- Review query performance metrics
- Update dashboards if needed

### Monthly
- Vacuum DuckDB
- Archive old event data
- Review and optimize slow queries

---

## Future Enhancements

Planned for Sprint 2:
- [ ] Query result caching (Redis)
- [ ] CSV/Excel export endpoints
- [ ] Alerting (email/Slack)
- [ ] More dashboards (HR, Procurement)
- [ ] GraphQL API
- [ ] Real-time WebSocket updates

---

## Documentation References

- **OLAP Worker API:** `/services/olap-worker/API.md`
- **DuckDB Schema:** `/services/olap-worker/migrations/README.md`
- **Grafana Dashboards:** `/grafana/DASHBOARDS.md`
- **Docker Compose:** `/docker-compose.bi.yml`

---

## Support

For issues or questions:
1. Check logs: `docker logs pulse-olap-worker`
2. Test API: `curl http://localhost:8004/health`
3. Review schema: `./services/olap-worker/migrations/migrate.sh status`
4. Check Grafana datasource: Settings → Data sources → OLAP Analytics → Test

---

**Version:** 1.0
**Last Updated:** 2025-10-04
**Maintained By:** Pulse ERP Team
