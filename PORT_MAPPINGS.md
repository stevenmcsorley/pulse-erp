# Pulse ERP - Port Mappings

This document lists all port mappings for Pulse ERP services, adjusted to avoid conflicts with existing services on this Raspberry Pi.

## 🔧 Port Changes Made

The following ports were changed from the original configuration to avoid conflicts:

| Service | Original Port | New Port | Reason |
|---------|--------------|----------|---------|
| Traefik Dashboard | 8080 | **8090** | Conflict with vid_stream-frontend |
| PostgreSQL | 5432 | **5434** | Conflict with jira-clone postgres |
| Grafana | 3000 | **3010** | Conflict with Gitea |
| MinIO API | 9000 | **9010** | Conflict with jira-clone MinIO |
| MinIO Console | 9001 | **9011** | Conflict with jira-clone MinIO console |
| Orders API | 8001 | **8011** | Conflict with vid_stream-backend |
| Inventory API | 8002 | **8012** | Conflict with vid_stream-video-processor |
| Billing API | 8003 | **8013** | Preventive (no conflict, but consistent numbering) |
| OLAP API | 8004 | **8014** | Preventive (no conflict, but consistent numbering) |

## 📡 Current Port Mapping

### Infrastructure Services (Base)

```
Traefik (Reverse Proxy)
├─ HTTP:              80   → 80
├─ HTTPS:             443  → 443
└─ Dashboard:         8090 → 8080 (internal)

PostgreSQL:           5434 → 5432 (internal)
NATS JetStream:       4222, 6222, 8222
MinIO S3:
├─ API:               9010 → 9000 (internal)
└─ Console:           9011 → 9001 (internal)

Prometheus:           9090
Grafana:              3010 → 3000 (internal)
```

### Application Services (ERP)

```
Frontend (Next.js):   3001 → 3000 (internal)
Orders Service:       8011 → 8001 (internal)
Inventory Service:    8012 → 8002 (internal)
Billing Service:      8013 → 8003 (internal)
OLAP Worker:          8014 → 8004 (internal)
```

## 🌐 Access URLs

### Local Access (Direct Port)

```bash
# Frontend Application
http://localhost:3001

# API Services
http://localhost:8011/docs  # Orders API (Swagger UI)
http://localhost:8012/docs  # Inventory API
http://localhost:8013/docs  # Billing API
http://localhost:8014/docs  # OLAP/Analytics API

# Infrastructure
http://localhost:3010       # Grafana Dashboards
http://localhost:8090       # Traefik Dashboard
http://localhost:9090       # Prometheus
http://localhost:9011       # MinIO Console
```

### Traefik Routing (.local domains)

If using `.local` domains (requires `/etc/hosts` or mDNS):

```bash
http://app.pulse-erp.local          # Frontend
http://grafana.pulse-erp.local      # Grafana
http://traefik.pulse-erp.local      # Traefik Dashboard
http://minio.pulse-erp.local        # MinIO Console
http://api.pulse-erp.local/orders   # Orders API (via Traefik)
```

## 🔒 Internal Container Communication

Services communicate internally using container names and internal ports:

```yaml
# Example from Orders Service
NATS_URL: nats://nats:4222
DB_HOST: postgres
DB_PORT: 5432  # Internal port, not 5434
```

## ⚠️ Important Notes

1. **External ports** (host machine) use the "New Port" column above
2. **Internal ports** (container-to-container) use original ports
3. PostgreSQL is accessed via **5434** from host, but **5432** from other containers
4. All API services expose Swagger UI at `/docs` endpoint
5. Traefik handles HTTPS termination and routing for production

## 🔍 Verify Services

```bash
# Check all Pulse ERP containers
docker ps | grep pulse

# Check specific service health
curl http://localhost:8011/health  # Orders
curl http://localhost:8012/health  # Inventory
curl http://localhost:8013/health  # Billing
curl http://localhost:8014/health  # OLAP

# Check Grafana
curl http://localhost:3010/api/health

# Check NATS
curl http://localhost:8222/healthz
```

## 📝 Environment Variables

The `.env` file contains updated URLs for the frontend:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8011
NEXT_PUBLIC_INVENTORY_API_URL=http://localhost:8012
NEXT_PUBLIC_BILLING_API_URL=http://localhost:8013
NEXT_PUBLIC_OLAP_API_URL=http://localhost:8014
NEXT_PUBLIC_GRAFANA_URL=http://localhost:3010
```

## 🔄 Updating Ports

If you need to change ports again:

1. Edit `/home/smcso/erp/docker-compose.base.yml` for infrastructure
2. Edit `/home/smcso/erp/docker-compose.services.yml` for ERP services
3. Update `/home/smcso/erp/.env` for frontend URLs
4. Restart affected services: `docker compose restart <service>`

---

**Last Updated:** October 4, 2025
**Configuration:** Raspberry Pi 5 with multiple Docker projects
