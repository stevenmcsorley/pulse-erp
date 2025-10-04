# ERP + BI Hybrid MVP — Trello Board Summary

## 📊 Board Overview

**Project:** ERP + BI Hybrid on Raspberry Pi 5
**Target:** Demo-ready MVP with real-time analytics
**Duration:** 2 Sprints (14 days)
**Hardware:** Raspberry Pi 5 (8GB RAM, 250GB SD, external SSD)

---

## 📋 Lists

1. **🎯 Epics / Roadmap** — 11 major epics
2. **📋 Backlog - Refined** — Prioritized tasks
3. **🚀 Sprint 1 — MVP (v0.1 Demo)** — 32 cards for first demo
4. **✨ Sprint 2 — Polish & Infra** — Auth, CI/CD, monitoring
5. **🔧 In Progress** — Active work
6. **👀 Review / QA** — Pending review
7. **✅ Done** — Completed work
8. **🚫 Blocked / Waiting** — Dependencies
9. **📦 Releases / Milestones** — v0.1, v0.2
10. **📚 Docs / Onboarding** — Documentation

---

## 🎯 Epics (11 Total)

### E01: Infrastructure Foundation (P0, Week 1 Days 0-1)
**Goal:** Provision Pi 5, Docker, base infrastructure (Postgres, NATS, MinIO, Traefik, monitoring)
**Cards:** C01-C07 (7 cards)
**Success:** All base services healthy, Prometheus scraping, HTTPS operational

### E02: Orders Service (P0, Week 1 Days 1-2)
**Goal:** Implement Orders API with Postgres persistence and NATS events
**Cards:** C08-C12 (5 cards)
**Success:** POST/GET/PATCH /orders functional, events emitted, 80%+ test coverage

### E03: Inventory Service (P0, Week 1 Day 2)
**Goal:** Product catalog, stock tracking, automated reservations
**Cards:** C13-C16 (4 cards)
**Success:** Stock reservation atomic, event-driven integration with Orders

### E04: Billing Service (P0, Week 1 Day 3)
**Goal:** Invoice generation, payments, ledger entries, PDF storage
**Cards:** C17-C20 (4 cards)
**Success:** Auto-invoice on order, payment flow, PDF in MinIO

### E05: OLAP & BI Pipeline (P0, Week 1 Days 4-5)
**Goal:** Stream consumers, DuckDB materialization, Grafana dashboards
**Cards:** C21-C25 (5 cards)
**Success:** <2s latency order → dashboard update, queries <500ms

### E06: Frontend UI (P0, Week 1-2 Days 3-6)
**Goal:** Next.js UI with order/inventory/billing forms, Grafana embed
**Cards:** C26-C31 (6 cards)
**Success:** Professional responsive UI, all demo flows functional

### E07: Auth & Security (P1, Week 2 Days 1-2)
**Goal:** Keycloak OAuth2/JWT, RBAC, secrets management
**Cards:** C32-C35 (4 cards)
**Success:** Multi-user auth, role enforcement, secrets secured

### E08: CI/CD & DevOps (P1, Week 2 Days 3-4)
**Goal:** Multi-arch builds, local registry, deployment automation, backups
**Cards:** C36-C40 (5 cards)
**Success:** Automated builds, one-command deploy, backup/restore tested

### E09: Monitoring & Observability (P1, Week 2 Day 5)
**Goal:** Metrics, dashboards, alerting, distributed tracing, logs
**Cards:** C41-C44 (4 cards)
**Success:** All services expose metrics, alerts configured, system dashboards

### E10: Testing & QA (P1, Week 2 Days 6-7)
**Goal:** Unit/integration/E2E tests, load testing
**Cards:** C45-C48 (4 cards)
**Success:** 80%+ coverage, E2E smoke tests, load test results

### E11: Demo Preparation (P0, Week 2 Day 7)
**Goal:** Seed data, rehearsal, documentation, presentation
**Cards:** C49-C52 (4 cards)
**Success:** 7-minute demo polished, cheat sheet ready, docs complete

---

## 🚀 Sprint 1 — MVP (v0.1 Demo) — 32 Cards

### Infrastructure (6 cards, 22pt)
- **C01** (3pt) — Provision Pi 5 + OS + Docker Setup
- **C02** (5pt) — Base Docker Compose (Postgres, NATS, MinIO, Traefik)
- **C03** (3pt) — Prometheus + Grafana Monitoring
- **C04** (5pt) — Database Schema Migrations
- **C05** *(backlog)* — Local Docker Registry Setup
- **C06** *(backlog)* — Traefik HTTPS Configuration

### Orders Service (5 cards, 24pt)
- **C08** (8pt) — Implement POST /orders endpoint
- **C09** (3pt) — Implement GET /orders/{id}
- **C10** (5pt) — Implement PATCH /orders/{id} status updates
- **C11** (3pt) — Orders Docker build (arm64)
- **C12** (5pt) — Orders integration tests

### Inventory Service (4 cards, 18pt)
- **C13** (5pt) — Implement product CRUD endpoints
- **C14** (5pt) — Implement stock reservation endpoint
- **C15** (5pt) — NATS consumer for order_created events
- **C16** (3pt) — Inventory Docker build + compose

### Billing Service (4 cards, 18pt)
- **C17** (5pt) — Implement invoice creation + auto-generation
- **C18** (5pt) — Implement payment endpoint + ledger
- **C19** (5pt) — PDF invoice generation (MinIO)
- **C20** (3pt) — Billing Docker build + compose

### OLAP & BI (5 cards, 24pt)
- **C21** (8pt) — OLAP worker NATS consumer
- **C22** (3pt) — DuckDB schema creation
- **C23** (5pt) — OLAP HTTP query API
- **C24** (5pt) — Grafana dashboards import
- **C25** (3pt) — BI stack docker-compose

### Frontend (6 cards, 32pt)
- **C26** (3pt) — Next.js setup + Tailwind
- **C27** (8pt) — Order creation form
- **C28** (8pt) — Inventory management UI
- **C29** (5pt) — Invoice list & payment UI
- **C30** (3pt) — Embed Grafana dashboards
- **C31** (5pt) — Frontend Docker build + Traefik routing

### Demo & Docs (4 cards, 19pt)
- **C49** (3pt) — Seed data script
- **C50** (8pt) — Playwright E2E smoke test
- **C51** (3pt) — Demo rehearsal & timing
- **C52** (5pt) — README & architecture docs

**Sprint 1 Total: 32 cards, ~157 story points**

---

## ✨ Sprint 2 — Polish & Infra (Backlog)

### Auth & Security (4 cards)
- **C32** — Keycloak setup + realm configuration
- **C33** — API Gateway JWT validation
- **C34** — RBAC implementation (admin/accountant/clerk)
- **C35** — Secrets management (Docker secrets / Vault)

### CI/CD & DevOps (5 cards)
- **C36** — GitHub Actions multi-arch build pipeline
- **C37** — Local Docker registry setup
- **C38** — Deployment automation scripts
- **C39** — Backup scripts (pg_dump + rclone)
- **C40** — Restore & disaster recovery testing

### Monitoring & Observability (4 cards)
- **C41** — Prometheus exporters for all services
- **C42** — Alert rules (low stock, failed payments)
- **C43** — Distributed tracing (OpenTelemetry + Jaeger)
- **C44** — Log aggregation (Loki + Promtail)

### Testing & QA (4 cards)
- **C45** — Unit test coverage >80%
- **C46** — Integration test suite
- **C47** — Load testing (100 concurrent users)
- **C48** — Security audit & penetration testing

---

## 📦 Releases

### M01: v0.1 MVP Demo (Sprint 1 Deliverable)
- **Target:** Day 7 (end of Sprint 1)
- **Scope:** Core ERP services, OLAP pipeline, Grafana dashboards, UI, demo script
- **Acceptance:**
  - All Sprint 1 cards completed
  - Demo rehearsed 3+ times successfully
  - Services stable >24 hours
  - Dashboard latency <2s
  - Memory usage <6GB

### M02: v0.2 Production-Ready (Sprint 2 Deliverable)
- **Target:** Day 14 (end of Sprint 2)
- **Scope:** Auth, CI/CD, backups, monitoring, security hardening
- **Acceptance:**
  - Keycloak auth functional
  - CI/CD automated
  - Backup/restore validated
  - Load test: 100 users, <500ms p95
  - Security audit passed

---

## 🎬 Sprint 1 Execution Plan (First 3 Days)

### Day 0: Infrastructure Setup
**Commands:**
```bash
# On fresh Pi 5
sudo apt update && sudo apt install -y docker.io docker-compose-plugin zram-tools
sudo usermod -aG docker $USER
sudo mkdir -p /mnt/ssd && sudo mount /dev/sda1 /mnt/ssd
echo "/dev/sda1 /mnt/ssd ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab

# Clone repo (or create)
git init erp-hybrid && cd erp-hybrid

# Create base compose stack
# (Work C02: create docker-compose.base.yml)
docker compose -f docker-compose.base.yml up -d

# Verify services
docker compose ps
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana
```

**Cards:** C01, C02, C03
**Outcome:** Base infrastructure running (Postgres, NATS, MinIO, Traefik, Prometheus, Grafana)

---

### Day 1: Orders Service + DB Schema
**Commands:**
```bash
# Run migrations
cd migrations && ./migrate.sh

# Build Orders service
cd orders-service
docker buildx build --platform linux/arm64 -t registry:5000/orders:latest --push .

# Start Orders service
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml up -d orders

# Test endpoint
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust-001","items":[{"sku":"CAM-1001","qty":3,"price":399.00}]}'
```

**Cards:** C04, C08, C09, C10, C11
**Outcome:** Orders API functional, events emitted to NATS

---

### Day 2: Inventory + Billing Services
**Commands:**
```bash
# Build Inventory service
cd inventory-service
docker buildx build --platform linux/arm64 -t registry:5000/inventory:latest --push .

# Build Billing service
cd billing-service
docker buildx build --platform linux/arm64 -t registry:5000/billing:latest --push .

# Start all ERP services
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml up -d

# Test end-to-end flow
curl -X POST http://localhost:8000/orders -d '...'  # Creates order
# Watch NATS events: nats sub "order.*"
# Verify invoice auto-created: curl http://localhost:8002/billing/invoices
```

**Cards:** C13, C14, C15, C16, C17, C18, C19, C20
**Outcome:** Full ERP stack operational, order → invoice flow working

---

### Day 3: OLAP Pipeline + Dashboards
**Commands:**
```bash
# Build OLAP worker
cd olap-worker
docker buildx build --platform linux/arm64 -t registry:5000/olap-worker:latest --push .

# Build OLAP query API
cd olap-query-api
docker buildx build --platform linux/arm64 -t registry:5000/olap-query-api:latest --push .

# Start BI stack
docker compose -f docker-compose.base.yml -f docker-compose.erp.yml -f docker-compose.bi.yml up -d

# Import Grafana dashboards
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/erp-sales.json

# Test OLAP query
curl "http://localhost:8001/query?sql=SELECT%20*%20FROM%20sales_by_hour"
```

**Cards:** C21, C22, C23, C24, C25
**Outcome:** Real-time analytics pipeline operational, Grafana dashboards live

---

## 📊 Key Metrics & Constraints

### Performance Targets
- **Dashboard latency:** <2s from order creation to dashboard update
- **OLAP query performance:** <500ms p95
- **API response time:** <200ms p95
- **Event processing:** <1s order → stock reservation

### Resource Constraints (Pi 5)
- **Total memory:** <6GB (leave 2GB for OS)
- **Postgres:** 2GB limit
- **NATS:** 512MB limit
- **MinIO:** 512MB limit
- **Each service:** 256-512MB limit
- **Storage:** Prioritize SSD for DB and OLAP data

### Test Coverage
- **Unit tests:** >70% per service
- **Integration tests:** All API endpoints
- **E2E tests:** Core demo flow automated
- **Load test:** 100 concurrent users, <500ms p95

---

## 🔧 Technical Stack Summary

### Infrastructure
- **OS:** Raspberry Pi OS 64-bit
- **Container:** Docker 24+, Compose v2
- **Ingress:** Traefik v2.11
- **Database:** PostgreSQL 15 (alpine)
- **Message Bus:** NATS 2.10 JetStream
- **Object Storage:** MinIO (latest)
- **Monitoring:** Prometheus + Grafana

### Services
- **Orders:** FastAPI (Python 3.11) or NestJS
- **Inventory:** FastAPI (Python 3.11) or NestJS
- **Billing:** FastAPI (Python 3.11) or NestJS
- **OLAP Worker:** Python 3.11 + DuckDB
- **OLAP Query API:** FastAPI + DuckDB

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Language:** TypeScript (strict mode)
- **Testing:** Playwright (E2E)

### Analytics
- **OLAP Store:** DuckDB (file-based)
- **Dashboards:** Grafana 10+
- **Query Engine:** DuckDB SQL

### CI/CD
- **Build:** Docker Buildx (multi-arch)
- **Registry:** Local Docker registry
- **Pipeline:** GitHub Actions (or Woodpecker)
- **Deployment:** docker-compose

---

## 📚 Documentation Deliverables

1. **README.md** — Setup instructions, prerequisites, quick start
2. **ARCHITECTURE.md** — System design, component descriptions, data flow
3. **API.md** — OpenAPI documentation, endpoint examples
4. **DATA_MODEL.md** — Database schema, table relationships
5. **DEMO_SCRIPT.md** — 7-minute demo walkthrough
6. **CONTRIBUTING.md** — Development workflow, PR guidelines
7. **TROUBLESHOOTING.md** — Common issues and solutions
8. **DEPLOYMENT.md** — Production deployment guide

---

## 🚦 Sprint 1 Success Criteria

### Technical
- ✅ All base infrastructure services healthy
- ✅ Orders, Inventory, Billing APIs functional
- ✅ NATS event-driven architecture operational
- ✅ DuckDB OLAP tables updated in real-time
- ✅ Grafana dashboards displaying live metrics
- ✅ Frontend UI complete with all demo flows
- ✅ E2E test passes consistently

### Operational
- ✅ Services stable for >24 hours
- ✅ Memory usage <6GB on Pi
- ✅ Dashboard latency <2s
- ✅ All docker-compose stacks start successfully
- ✅ Backup script tested (pg_dump + restore)

### Demo
- ✅ Demo script rehearsed 3+ times
- ✅ Seed data loads in <30s
- ✅ All demo steps complete in <7 minutes
- ✅ Recovery procedures documented
- ✅ Presenter cheat sheet ready

### Documentation
- ✅ README with complete setup instructions
- ✅ Architecture documentation with diagrams
- ✅ API documentation generated
- ✅ Demo script finalized
- ✅ All code reviewed and merged

---

## 🔗 Dependencies Map

```
C01 (Pi Provision)
 └─> C02 (Base Compose)
      ├─> C03 (Monitoring)
      ├─> C04 (Migrations)
      │    └─> C08 (Orders POST)
      │         ├─> C09 (Orders GET)
      │         ├─> C10 (Orders PATCH)
      │         ├─> C11 (Orders Docker)
      │         ├─> C12 (Orders Tests)
      │         ├─> C15 (Inventory Consumer)
      │         └─> C17 (Billing Auto-Invoice)
      │
      ├─> C13 (Inventory CRUD)
      │    └─> C14 (Stock Reserve)
      │         └─> C15 (Inventory Consumer)
      │              └─> C16 (Inventory Docker)
      │
      ├─> C17 (Billing Invoice)
      │    └─> C18 (Billing Payment)
      │         └─> C19 (PDF Generation)
      │              └─> C20 (Billing Docker)
      │
      ├─> C21 (OLAP Worker)
      │    └─> C22 (DuckDB Schema)
      │         └─> C23 (OLAP Query API)
      │              └─> C24 (Grafana Dashboards)
      │                   └─> C25 (BI Compose)
      │
      └─> C26 (Frontend Setup)
           ├─> C27 (Order Form)
           ├─> C28 (Inventory UI)
           ├─> C29 (Billing UI)
           ├─> C30 (Dashboard Embed)
           └─> C31 (Frontend Docker)
                └─> C49 (Seed Data)
                     └─> C50 (E2E Tests)
                          └─> C51 (Demo Rehearsal)
                               └─> C52 (Docs)
```

---

## 📋 Card Format Reference

Each card includes:
- **Title:** Clear, imperative task description
- **Description:** Summary, references, deliverables, code examples
- **Labels:** Component (frontend/api/infra/bi/data/qa/docs), Priority (P0/P1/P2), Estimate (story points)
- **Checklists:** Implementation, Testing, Security/Demo steps
- **Acceptance Criteria:** Explicit, testable conditions
- **Estimate:** Story points (Fibonacci: 1, 2, 3, 5, 8, 13)
- **Branch Template:** `feature/`, `ci/`, `test/`, `docs/`, `demo/`
- **PR Title Template:** Conventional Commits format (`feat:`, `fix:`, `test:`, `docs:`, `ci:`)
- **Dependencies:** Card IDs or "blocked by" references
- **Assignees:** `@frontend`, `@backend`, `@devops`, `@qa`, `@bi`, `@data`, `@lead`
- **Reviewers:** Required reviewers by role

---

## 🎯 Next Steps

1. **Import Trello JSON:** Use `trello-board.json` with Trello import tool
2. **Assign Team Members:** Map placeholder roles to actual team members
3. **Sprint Planning:** Move Sprint 1 cards to backlog, prioritize for Day 0-7
4. **Setup Pi Environment:** Follow C01 instructions to provision hardware
5. **Start Development:** Begin with C01 → C02 → C04 → C08 in sequence
6. **Daily Standups:** Track progress, update card status, address blockers
7. **Demo Prep:** Begin rehearsals on Day 5, finalize by Day 7

---

**Total Cards:** 52 (32 Sprint 1 + 17 Sprint 2 + 2 Milestones + 1 backlog)
**Total Story Points (Sprint 1):** ~157pt
**Estimated Velocity:** ~22pt/day (7-day sprint)
**Buffer:** 15% (built into estimates)

---

## 📞 Support & Resources

- **Trello Board JSON:** `/home/smcso/erp/trello-board.json`
- **Project Docs:** PRD, SAD, OpenAPI, Data Model, Demo Script, Style Guide
- **Issue Tracking:** GitHub Issues (or Trello comments)
- **Team Communication:** Slack/Discord (configure channels per epic)

---

*Generated for ERP + BI Hybrid MVP — Raspberry Pi 5 Demo Project*
*Last Updated: 2025-10-04*
