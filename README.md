# Pulse ERP

**Modular ERP with Real-time Business Intelligence**

A self-hosted ERP system with integrated streaming analytics, designed to run on Raspberry Pi 5 (arm64) and scale to production environments.

## 🎯 Project Overview

Pulse ERP combines traditional ERP functionality (Orders, Inventory, Billing, HR) with a real-time BI pipeline that provides instant business insights through streaming data architecture.

**Key Features:**
- 📦 **Order Management** — Full order lifecycle with event-driven workflows
- 📊 **Inventory Control** — Stock tracking, reservations, and low-stock alerts
- 💰 **Billing & Accounting** — Automated invoicing, payments, and ledger entries
- 📈 **Real-time Analytics** — <2s latency from transaction to dashboard update
- 🔄 **Event-Driven Architecture** — NATS JetStream for reliable event streaming
- 🐳 **Docker-First** — Fully containerized, arm64 optimized
- 🔒 **Security Built-in** — OAuth2/JWT authentication with RBAC

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ Next.js 14 + Tailwind
│   (Next.js) │
└──────┬──────┘
       │
┌──────▼──────────────────────────────┐
│         API Gateway                 │
│      (FastAPI / Traefik)            │
└──────┬──────────────────────────────┘
       │
   ┌───┴────┬────────┬─────────┐
   │        │        │         │
┌──▼───┐ ┌─▼──┐  ┌──▼────┐ ┌──▼───┐
│Orders│ │Inv.│  │Billing│ │ HR   │
└──┬───┘ └─┬──┘  └──┬────┘ └──┬───┘
   │       │        │         │
   └───────┴────┬───┴─────────┘
                │
         ┌──────▼──────┐
         │    NATS     │ Event Stream
         │ JetStream   │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │ OLAP Worker │ Stream Consumer
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │   DuckDB    │ Analytics Store
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │   Grafana   │ Dashboards
         └─────────────┘
```

## 🚀 Quick Start (Raspberry Pi 5)

### Prerequisites
- Raspberry Pi 5 (8GB RAM recommended)
- Raspberry Pi OS 64-bit
- External SSD (recommended for database/OLAP storage)
- Docker & Docker Compose

### Installation

```bash
# Clone repository
git clone https://github.com/stevenmcsorley/pulse-erp.git
cd pulse-erp

# Run setup script (provisions Pi, installs Docker)
./scripts/setup-pi.sh

# Start base infrastructure
docker compose -f docker-compose.base.yml up -d

# Run database migrations
./migrations/migrate.sh

# Start ERP services
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml up -d

# Start BI stack
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml up -d
```

Access the application:
- **Frontend UI:** https://app.local (or your configured domain)
- **Grafana Dashboards:** https://grafana.local
- **Traefik Dashboard:** https://traefik.local

## 📁 Project Structure

```
pulse-erp/
├── services/
│   ├── orders/              # Orders microservice
│   ├── inventory/           # Inventory microservice
│   ├── billing/             # Billing microservice
│   ├── hr/                  # HR microservice (minimal MVP)
│   ├── olap-worker/         # OLAP stream consumer
│   └── olap-query-api/      # DuckDB query API
├── frontend/                # Next.js frontend application
├── migrations/              # Database migration scripts
├── grafana/                 # Grafana dashboards & config
├── docker-compose.base.yml  # Base infrastructure
├── docker-compose.erp.yml   # ERP services
├── docker-compose.bi.yml    # BI/OLAP stack
├── scripts/                 # Deployment & utility scripts
└── docs/                    # Documentation
```

## 🛠️ Technology Stack

**Infrastructure:**
- Docker & Docker Compose
- Traefik (Ingress/TLS)
- PostgreSQL 15
- NATS JetStream
- MinIO (S3-compatible storage)

**Backend Services:**
- FastAPI (Python 3.11) or NestJS (TypeScript)
- NATS client libraries
- PostgreSQL drivers

**Frontend:**
- Next.js 14 (App Router)
- TypeScript (strict mode)
- Tailwind CSS
- React Hook Form

**Analytics:**
- DuckDB (OLAP store)
- Grafana 10+
- Prometheus (metrics)

**Monitoring:**
- Prometheus
- Grafana
- Loki (logs)
- Jaeger (distributed tracing)

## 📊 Demo Flow

1. **Create Product** → Add `CAM-1001` to inventory with stock level 10
2. **Create Customer** → Add `Acme Corp`
3. **Place Order** → Order 3x `CAM-1001` for £1,197
4. **Auto-Reserve Stock** → Inventory automatically reserves 3 units
5. **Auto-Generate Invoice** → Billing service creates invoice
6. **Mark Paid** → Payment recorded, ledger updated
7. **Dashboard Updates** → Grafana shows sales spike in <2 seconds

## 🧪 Development

### Running Tests

```bash
# Unit tests (all services)
./scripts/test-unit.sh

# Integration tests
./scripts/test-integration.sh

# E2E tests (Playwright)
cd frontend && npm run test:e2e

# Load tests
./scripts/test-load.sh
```

### Local Development

```bash
# Start services in development mode
docker compose -f docker-compose.dev.yml up

# Watch logs for specific service
docker compose logs -f orders

# Rebuild specific service
docker compose up -d --build orders
```

## 📈 Performance Targets

- **Dashboard Latency:** <2s from order creation to dashboard update
- **API Response Time:** <200ms p95
- **OLAP Query Performance:** <500ms p95
- **Event Processing:** <1s order → stock reservation
- **Memory Footprint:** <6GB total on Pi 5

## 🔒 Security

- HTTPS everywhere (Traefik auto-certificates)
- OAuth2/JWT authentication (Keycloak)
- Role-based access control (admin, accountant, clerk)
- Secrets management (Docker secrets)
- Audit logging for all financial transactions

## 📚 Documentation

- [Architecture Document](./docs/ARCHITECTURE.md)
- [API Documentation](./docs/API.md)
- [Data Model](./docs/DATA_MODEL.md)
- [Demo Script](./docs/DEMO_SCRIPT.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Troubleshooting](./docs/TROUBLESHOOTING.md)

## 🗓️ Roadmap

### v0.1 MVP (Sprint 1) ✅
- Core ERP services (Orders, Inventory, Billing)
- OLAP pipeline with real-time dashboards
- Frontend UI with all demo flows
- Docker deployment on Pi 5

### v0.2 Production Ready (Sprint 2)
- Authentication & RBAC
- CI/CD pipeline
- Automated backups
- Comprehensive monitoring
- Load tested (100 concurrent users)

### v0.3 Future Enhancements
- Multi-currency support
- Advanced reporting
- Mobile app
- Kubernetes deployment

## 🤝 Contributing

See [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for development workflow and coding standards.

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details

## 🙏 Acknowledgments

Built with modern open-source technologies:
- PostgreSQL, NATS, DuckDB
- Next.js, FastAPI, Docker
- Grafana, Prometheus, Traefik

---

**Demo-ready on Raspberry Pi 5 | Production-ready architecture | Event-driven design**
