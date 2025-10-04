# Pulse ERP

**A modern, event-driven ERP system built for small businesses**

Full-stack application showcasing microservices architecture, real-time analytics, and modern web technologies - all running on a Raspberry Pi 5.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Raspberry Pi 5](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red)](https://www.raspberrypi.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)
[![Tests](https://img.shields.io/badge/Tests-Playwright-green)](e2e/)

## 🎯 Project Overview

Pulse ERP is a demonstration-grade Enterprise Resource Planning system showcasing modern software architecture patterns. It provides core ERP functionality with real-time business intelligence.

**Core Features:**
- 📦 **Order Management** — Create, track, and fulfill customer orders
- 📊 **Inventory Control** — Product catalog, stock levels, and automatic reservations
- 💰 **Billing & Invoicing** — Auto-generate invoices on order placement, track payments
- 📈 **Real-time Analytics** — Business intelligence dashboards with 10-second refresh
- 🔄 **Event-Driven Architecture** — NATS JetStream for service decoupling
- 🐳 **Docker-First** — Fully containerized, arm64 optimized for Raspberry Pi
- ✅ **Production Patterns** — CQRS, event sourcing, health checks, monitoring

**What's Included:**
- ✅ Complete backend (Orders, Inventory, Billing, OLAP)
- ✅ Modern Next.js 14 frontend with TypeScript
- ✅ Grafana dashboards (Sales, Inventory, Cashflow)
- ✅ Seed data generator for instant demo
- ✅ Playwright E2E tests covering full demo flow
- ✅ Comprehensive deployment documentation

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

### Backend
- **FastAPI** (Python 3.11) - REST APIs with OpenAPI/Swagger
- **PostgreSQL 16** - OLTP transactional database
- **DuckDB** - OLAP analytics database (in-process)
- **NATS JetStream** - Event streaming and message durability
- **Pydantic** - Data validation and serialization

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development (strict mode)
- **Tailwind CSS** - Utility-first styling with dark mode
- **Axios** - HTTP client for API communication

### Infrastructure
- **Docker & Docker Compose** - Containerization and orchestration
- **Traefik** - Reverse proxy, load balancer, HTTPS termination
- **Grafana 10+** - Dashboards and visualization
- **Prometheus** - Metrics collection and storage

### Testing
- **Playwright** - End-to-end browser testing
- **pytest** - Python unit testing framework

### Development Tools
- **uvicorn** - ASGI server for FastAPI
- **TypeScript ESLint** - Code linting
- **Black** - Python code formatting

## 📊 Demo Flow (7 Minutes)

1. **Create Product** → Add `DEMO-CAM-500` to inventory
2. **Set Stock Level** → Use quick actions to set 100 units
3. **Create Order** → Order 5 units for $2,499.95
4. **Place Order** → Changes status from draft → placed
5. **Verify Stock Reservation** → Check 5 units reserved automatically
6. **Auto-Generated Invoice** → Billing service created invoice async
7. **Mark as Paid** → Record payment via UI
8. **View Analytics** → Grafana dashboards update within 10 seconds

**Run the demo:**
```bash
# Load seed data first
./scripts/seed_demo.sh

# Follow the script
open demo/DEMO_SCRIPT.md

# Or run automated E2E test
cd e2e && npm test
```

See [demo/DEMO_SCRIPT.md](demo/DEMO_SCRIPT.md) for complete walkthrough with timing.

## 🧪 Testing

### End-to-End Tests

Complete demo flow automated with Playwright:

```bash
cd e2e
npm install
npx playwright install --with-deps chromium
npm test
```

**Run in headed mode** (see browser):
```bash
npm run test:headed
```

**View test report:**
```bash
npm run report
```

See [e2e/README.md](e2e/README.md) for details.

### Development

**Backend service development:**
```bash
cd services/orders
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

**Frontend development:**
```bash
cd frontend
npm install
npm run dev
```

**View logs:**
```bash
docker logs -f pulse-orders
docker logs -f pulse-frontend
```

## 🔌 API Endpoints

### Orders Service (Port 8001)
- `POST /orders` - Create new order
- `GET /orders` - List all orders
- `GET /orders/{id}` - Get order details
- `PATCH /orders/{id}` - Update order status

### Inventory Service (Port 8002)
- `POST /products` - Create product
- `GET /products` - List products
- `GET /products/{sku}` - Get product details
- `PUT /inventory/{sku}` - Update stock levels
- `GET /inventory` - List all inventory

### Billing Service (Port 8003)
- `GET /invoices` - List invoices
- `GET /invoices/{id}` - Get invoice details
- `POST /invoices/{id}/pay` - Mark invoice as paid

### OLAP Service (Port 8004)
- `GET /sales/hourly?hours=24` - Hourly sales metrics
- `GET /inventory/low-stock` - Low stock alerts
- `GET /ar/overdue` - Overdue accounts receivable
- `GET /orders/daily?days=30` - Daily order stats

**Interactive API Documentation:** http://localhost:8001/docs (Swagger UI)

## 🔧 Configuration

### Environment Variables

Create `.env` file (see `.env.example`):

```bash
# Database
POSTGRES_DB=pulse_erp
POSTGRES_USER=pulseadmin
POSTGRES_PASSWORD=changeme

# Domain (for Traefik routing)
DOMAIN=localhost

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin
GF_AUTH_ANONYMOUS_ENABLED=true
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3001 | Next.js UI |
| Orders | 8001 | Orders API + Swagger |
| Inventory | 8002 | Inventory API |
| Billing | 8003 | Billing API |
| OLAP | 8004 | Analytics API |
| Grafana | 3000 | Dashboards |
| Prometheus | 9090 | Metrics |
| PostgreSQL | 5432 | Database |
| NATS | 4222 | Event Bus |

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide with options
- **[DEMO_SCRIPT.md](demo/DEMO_SCRIPT.md)** - 7-minute demo walkthrough with timing
- **[CHEAT_SHEET.md](demo/CHEAT_SHEET.md)** - Quick reference for demo
- **[E2E Tests](e2e/README.md)** - Playwright test documentation
- **[Scripts](scripts/README.md)** - Utility scripts (seed data, migrations)

## 🗓️ Roadmap

### ✅ v0.1 MVP (Sprint 1) - COMPLETE

**Backend:**
- [x] Orders Service (C08-C11)
- [x] Inventory Service (C13-C16)
- [x] Billing Service (C17, C20)
- [x] OLAP Worker & Query API (C21-C23)
- [x] Grafana Dashboards (C24)
- [x] Docker Compose deployment (C25)

**Frontend:**
- [x] Next.js setup (C26)
- [x] Order management UI (C27)
- [x] Inventory management UI (C28)
- [x] Invoice & payment UI (C29)
- [x] Grafana dashboard embeds (C30)
- [x] Docker build & Traefik routing (C31)

**Demo & Testing:**
- [x] Seed data script (C49)
- [x] Playwright E2E tests (C50)
- [x] Demo script & materials (C51)
- [x] Documentation (C52)

### 📋 v0.2 Production Ready (Sprint 2 - Backlog)

- [ ] Keycloak authentication (C32)
- [ ] JWT validation & RBAC (C33-C34)
- [ ] Secrets management (C35)
- [ ] GitHub Actions CI/CD (C36)
- [ ] Backup & restore procedures (C39-C40)
- [ ] Prometheus exporters (C41)
- [ ] Alert rules (C42)
- [ ] Integration test coverage >80% (C12, C46)
- [ ] Payment endpoint + ledger (C18)
- [ ] PDF invoice generation (C19)

### 🚀 v0.3 Future Enhancements

- [ ] Distributed tracing (Jaeger)
- [ ] Log aggregation (Loki)
- [ ] Load testing validation
- [ ] Multi-currency support
- [ ] Advanced reporting
- [ ] Kubernetes deployment configs

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker status
docker ps | grep pulse

# View logs
docker logs pulse-orders

# Restart specific service
docker-compose restart orders
```

### Frontend not accessible
```bash
# Check if running
curl http://localhost:3001

# Rebuild and restart
cd frontend
docker build -t pulse-frontend .
docker-compose up -d frontend
```

### Database errors
```bash
# Check PostgreSQL
docker exec -it postgres psql -U pulseadmin -d pulse_erp -c '\dt'

# Re-run migrations
./scripts/migrate.sh
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive troubleshooting guide.

## 🤝 Contributing

This is a demonstration project, but contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details

## 🙏 Acknowledgments

Built with modern open-source technologies:
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Next.js](https://nextjs.org/)** - React framework for production
- **[DuckDB](https://duckdb.org/)** - In-process OLAP database
- **[NATS](https://nats.io/)** - Cloud-native messaging system
- **[Grafana](https://grafana.com/)** - Observability platform
- **[PostgreSQL](https://www.postgresql.org/)** - World's most advanced open source database
- **[Traefik](https://traefik.io/)** - Modern HTTP reverse proxy
- **[Playwright](https://playwright.dev/)** - Reliable end-to-end testing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

**Project Repository:** [github.com/stevenmcsorley/pulse-erp](https://github.com/stevenmcsorley/pulse-erp)

---

**✨ Built to demonstrate modern ERP architecture on affordable hardware**

*Demo-ready | Production patterns | Event-driven | Self-hosted*
