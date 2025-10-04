# Pulse ERP - 7-Minute Demo Script

**Target Time:** 6:30-7:00 minutes
**Audience:** Technical stakeholders, potential clients, investors
**Goal:** Demonstrate full-stack ERP system with real-time analytics

---

## Pre-Demo Setup (5 minutes before)

**✅ Checklist:**
- [ ] All services running (`docker ps | grep pulse`)
- [ ] Seed data loaded (`./scripts/seed_demo.sh`)
- [ ] Frontend accessible (http://localhost:3001)
- [ ] Grafana dashboards loaded (http://localhost:3000)
- [ ] Terminal ready with commands
- [ ] Browser tabs open and positioned
- [ ] Backup plan ready (screenshots in `demo/screenshots/`)

---

## Demo Flow

### INTRODUCTION (0:00 - 0:30) | 30 seconds

**Script:**
> "Good morning/afternoon. I'm going to demonstrate Pulse ERP - a modern, event-driven ERP system built for small businesses. This is a full-stack application running entirely on a Raspberry Pi 5, showcasing microservices, real-time analytics, and a modern React frontend."

**Key Points:**
- Full-stack MVP
- Event-driven architecture
- Real-time analytics
- Self-hosted on Raspberry Pi 5

---

### PART 1: SYSTEM OVERVIEW (0:30 - 1:30) | 1 minute

**Script:**
> "Let me show you the architecture. We have three core microservices: Orders, Inventory, and Billing. They communicate via NATS JetStream for event streaming. Every transaction is captured and streamed to our OLAP database - DuckDB - which powers real-time dashboards in Grafana."

**Show:**
1. Open `DEPLOYMENT.md` - scroll to architecture diagram
2. Highlight key components:
   - Frontend (Next.js)
   - API Services (FastAPI)
   - Event Bus (NATS)
   - OLAP Pipeline (DuckDB)
   - Dashboards (Grafana)

**Key Points:**
- Microservices architecture
- Event-driven design
- OLTP → NATS → OLAP pipeline
- Zero data loss

**Timing Check:** 1:30 elapsed

---

### PART 2: INVENTORY MANAGEMENT (1:30 - 3:00) | 1.5 minutes

**Script:**
> "Let's start with inventory. I'll create a new product, set stock levels, and you'll see how the system tracks everything in real-time."

**Demo Steps:**

1. **Navigate to Inventory** (10s)
   - Open http://localhost:3001/inventory
   - Show product list with existing products
   - Point out low stock indicators

2. **Create New Product** (30s)
   - Click "+ Add Product"
   - Fill form:
     - SKU: `DEMO-CAM-500`
     - Name: `Demo Security Camera`
     - Price: `499.99`
   - Click "Create Product"
   - Verify redirect to inventory list

3. **Set Stock Level** (30s)
   - Click "Adjust Stock" for new product
   - Show current stock (0 units)
   - Use quick actions: Click "+50" twice
   - Verify: 100 units on hand

4. **Show Inventory Stats** (20s)
   - Return to inventory list
   - Point out:
     - Total products
     - Low stock items (if any)
     - Total units

**Key Points:**
- Simple, intuitive UI
- Real-time stock tracking
- Quick actions for efficiency
- Low stock alerts

**Timing Check:** 3:00 elapsed

---

### PART 3: ORDER CREATION & FULFILLMENT (3:00 - 5:00) | 2 minutes

**Script:**
> "Now let's create an order. This will trigger our event stream: the order goes to inventory for stock reservation, then to billing for invoice generation."

**Demo Steps:**

1. **Create Order** (45s)
   - Navigate to `/orders/new`
   - Fill form:
     - Customer ID: `DEMO-CUSTOMER-001`
     - Select product: `DEMO-CAM-500`
     - Quantity: `5`
   - Show total calculation (5 × $499.99 = $2,499.95)
   - Click "Create Order"

2. **Place Order** (30s)
   - On order detail page, click "Place Order"
   - Explain: This changes status from draft → placed
   - Point out: Order ID, customer, total amount

3. **Verify Stock Reservation** (20s)
   - Navigate back to inventory
   - Show `DEMO-CAM-500`:
     - On Hand: 100
     - Reserved: 5
     - Available: 95
   - Explain: Stock is reserved, not yet shipped

4. **Show Invoice Auto-Generation** (25s)
   - Navigate to `/invoices`
   - Find invoice with matching order ID
   - Click to view invoice detail
   - Show:
     - Amount: $2,499.95
     - Status: Issued
     - Due date (30 days)
     - Line items from order

**Key Points:**
- Event-driven workflow
- Automatic stock reservation
- Auto-invoice generation
- Consistent data across services

**Timing Check:** 5:00 elapsed

---

### PART 4: PAYMENT & ANALYTICS (5:00 - 6:30) | 1.5 minutes

**Script:**
> "Let's complete the payment and see how our analytics update in real-time."

**Demo Steps:**

1. **Mark Invoice as Paid** (30s)
   - On invoice detail page
   - Click "Mark as Paid"
   - Confirm in modal
   - Verify status changes to "Paid"
   - Show paid timestamp

2. **Navigate to Dashboards** (15s)
   - Go to `/dashboards`
   - Show three dashboard cards:
     - Sales Analytics
     - Inventory Status
     - Cashflow & AR

3. **Show Sales Dashboard** (30s)
   - Click "Sales Analytics"
   - Wait for Grafana to load
   - Point out:
     - Hourly revenue chart
     - Order volume
     - Top products
     - Today's totals
   - Explain: "This updates every 10 seconds from our OLAP database"

4. **Show Inventory Dashboard** (15s)
   - Switch to "Inventory Status"
   - Point out:
     - Low stock alerts
     - Stock movement trends
     - Product categories

**Key Points:**
- Real-time payment processing
- Instant analytics updates
- Business intelligence dashboards
- 10-second refresh rate

**Timing Check:** 6:30 elapsed

---

### CLOSING (6:30 - 7:00) | 30 seconds

**Script:**
> "So in under 7 minutes, we've created a product, managed inventory, processed an order, generated an invoice, recorded payment, and seen real-time analytics - all on a $100 Raspberry Pi. This demonstrates the power of modern microservices, event streaming, and OLAP analytics for small businesses."

**Final Points:**
- Complete ERP workflow
- Event-driven architecture
- Real-time analytics
- Cost-effective deployment (Raspberry Pi 5)
- Open-source stack
- Production-ready patterns

**Call to Action:**
> "The entire codebase is on GitHub. Feel free to explore the architecture, run it locally, or deploy it to your own infrastructure. Questions?"

---

## Backup Plan

### If Services Are Down

**Option 1: Show Screenshots**
- Navigate to `demo/screenshots/`
- Walk through each step with screenshots
- Explain what would happen

**Option 2: Show E2E Test**
```bash
cd e2e
npm run test:headed
```
- Run Playwright test in headed mode
- Explain each step as it executes
- Show test passing

### If Frontend Is Slow

**Option 3: Direct API Demo**
```bash
# Show products
curl http://localhost:8002/products | jq

# Create order
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "API-DEMO",
    "items": [{"sku": "CAM-1001", "qty": 2, "price": 299.99}]
  }' | jq

# Show analytics
curl http://localhost:8004/sales/hourly?hours=24 | jq
```

---

## Q&A Preparation

### Common Questions

**Q: How does the event streaming work?**
> A: When an order is placed, we publish an `order_created` event to NATS JetStream. The inventory service consumes this event and reserves stock. The billing service also consumes it to generate an invoice. The OLAP worker captures all events for analytics. This decouples services and ensures consistency.

**Q: Why DuckDB instead of PostgreSQL for analytics?**
> A: DuckDB is optimized for OLAP workloads - complex aggregations, analytics queries. PostgreSQL handles OLTP - transactions, updates. We use both: Postgres for transactional data, DuckDB for analytics. DuckDB can query billions of rows in milliseconds.

**Q: How do you handle failures?**
> A: Each service has health checks. NATS provides message durability - if a consumer is down, messages are retained. We use idempotent operations, so replaying events is safe. Docker restart policies ensure services recover automatically.

**Q: Can this scale beyond a Raspberry Pi?**
> A: Absolutely. The Docker Compose files are layered - you can deploy services independently to any cloud provider. Kubernetes configs would be the next step. NATS and DuckDB both scale horizontally. We've architected for growth.

**Q: What about security?**
> A: Currently, this is a demo without authentication. Production would add Keycloak (OAuth2/OIDC), API rate limiting, encrypted connections, secrets management with Vault, and RBAC policies. The architecture supports it - we just haven't implemented it for the MVP.

**Q: How long did this take to build?**
> A: From scratch to this demo: approximately 2 weeks of development. The event-driven architecture took time to design, but it pays off in maintainability and scalability.

---

## Recovery Procedures

### Restart Services
```bash
docker-compose -f docker-compose.base.yml -f docker-compose.services.yml down
docker-compose -f docker-compose.base.yml -f docker-compose.services.yml up -d
```

### Reset Data
```bash
docker-compose down -v
docker-compose up -d
./scripts/migrate.sh
./scripts/seed_demo.sh
```

### Check Logs
```bash
docker logs pulse-orders --tail 50
docker logs pulse-inventory --tail 50
docker logs pulse-billing --tail 50
```

---

## Tips for Success

1. **Practice 3+ times** before the real demo
2. **Time yourself** - aim for 6:30-6:45
3. **Have backup screenshots** ready
4. **Test all URLs** before starting
5. **Close unnecessary apps** to ensure performance
6. **Have a second browser** ready as backup
7. **Rehearse Q&A answers** out loud
8. **Stay calm** - if something breaks, pivot to backup plan
9. **Engage the audience** - ask if they can see the screen
10. **End with energy** - this is impressive work!

---

## Post-Demo Notes

After the demo, be ready to discuss:
- **GitHub repository** structure
- **Deployment options** (cloud vs. on-prem)
- **Cost analysis** (Raspberry Pi vs. cloud)
- **Technology choices** (FastAPI, Next.js, DuckDB)
- **Event-driven patterns** (saga, CQRS)
- **Future roadmap** (Keycloak, CI/CD, monitoring)
