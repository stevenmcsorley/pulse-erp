# Pulse ERP - Demo Cheat Sheet

Quick reference for demo presentation. Print this out!

---

## Quick Access URLs

```
Frontend:       http://localhost:3001
Grafana:        http://localhost:3000
Prometheus:     http://localhost:9090

Orders API:     http://localhost:8001
Inventory API:  http://localhost:8002
Billing API:    http://localhost:8003
OLAP API:       http://localhost:8004
```

---

## Pre-Demo Commands

```bash
# Check services
docker ps | grep pulse

# View logs
docker logs pulse-orders --tail 20

# Seed data
./scripts/seed_demo.sh

# Test frontend
curl http://localhost:3001

# Test APIs
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

---

## Demo Data

**Test Product:**
- SKU: `DEMO-CAM-500`
- Name: `Demo Security Camera`
- Price: `$499.99`
- Initial Stock: `100 units`

**Test Customer:**
- ID: `DEMO-CUSTOMER-001`

**Test Order:**
- Quantity: `5 units`
- Total: `$2,499.95`

---

## Demo Flow Timeline

| Time | Section | Key Action |
|------|---------|------------|
| 0:00 | Intro | Introduce Pulse ERP |
| 0:30 | Architecture | Show diagram |
| 1:30 | Inventory | Create product |
| 2:00 | Stock | Set 100 units |
| 3:00 | Order | Create order |
| 3:45 | Fulfillment | Place order |
| 4:05 | Verify | Check stock reserved |
| 4:30 | Invoice | Show auto-invoice |
| 5:00 | Payment | Mark as paid |
| 5:30 | Analytics | Open dashboards |
| 6:00 | Sales Dashboard | Show charts |
| 6:30 | Close | Summary & Q&A |

**Target:** 6:30-7:00 minutes

---

## Navigation Path

1. `/inventory` → View products
2. `/inventory/products/new` → Create product
3. `/inventory/stock/DEMO-CAM-500` → Adjust stock
4. `/orders/new` → Create order
5. `/orders/{id}` → Order detail
6. `/inventory` → Verify reservation
7. `/invoices` → Find invoice
8. `/invoices/{id}` → Invoice detail
9. `/dashboards` → View analytics
10. Switch to Sales dashboard

---

## Key Talking Points

### Architecture
- "3 microservices: Orders, Inventory, Billing"
- "Event-driven with NATS JetStream"
- "OLTP → NATS → OLAP pipeline"
- "Real-time analytics with DuckDB"

### Inventory
- "Simple, intuitive UI"
- "Real-time stock tracking"
- "Low stock alerts"
- "Quick actions for efficiency"

### Orders
- "Event-driven workflow"
- "Automatic stock reservation"
- "Auto-invoice generation"
- "Consistent data across services"

### Analytics
- "Real-time updates every 10 seconds"
- "Business intelligence dashboards"
- "Zero data loss"
- "OLAP-optimized queries"

### Closing
- "Complete ERP workflow in <7 minutes"
- "Running on $100 Raspberry Pi"
- "Production-ready patterns"
- "Open-source stack"

---

## Backup Plans

### Plan A: Services Down
Navigate to `demo/screenshots/` and walk through images

### Plan B: Frontend Slow
Run E2E test in headed mode:
```bash
cd e2e
npm run test:headed
```

### Plan C: Total Failure
Show API responses directly:
```bash
# Products
curl http://localhost:8002/products | jq

# Create order
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"API","items":[{"sku":"CAM-1001","qty":2,"price":299.99}]}' | jq

# Analytics
curl http://localhost:8004/sales/hourly?hours=1 | jq
```

---

## Common Questions (Quick Answers)

**Q: Event streaming?**
"NATS JetStream. Order placed → inventory reserves stock → billing creates invoice. Decoupled, durable, fast."

**Q: Why DuckDB?**
"OLAP-optimized. Billions of rows in milliseconds. PostgreSQL for OLTP, DuckDB for analytics."

**Q: Failure handling?**
"Health checks, message durability, idempotent operations, Docker restart policies."

**Q: Scalability?**
"Docker Compose now, Kubernetes next. NATS and DuckDB scale horizontally. Architected for growth."

**Q: Security?**
"Demo has none. Production adds Keycloak (OAuth2), rate limiting, TLS, Vault, RBAC."

**Q: Build time?**
"2 weeks from scratch. Event-driven architecture took design time, but worth it."

---

## Recovery Commands

### Restart Everything
```bash
docker-compose -f docker-compose.base.yml \
  -f docker-compose.services.yml \
  -f docker-compose.bi.yml \
  -f docker-compose.erp.yml \
  restart
```

### Reset Data
```bash
docker-compose down -v
docker-compose up -d
./scripts/migrate.sh
./scripts/seed_demo.sh
```

### Check Service Health
```bash
for port in 8001 8002 8003 8004 3001; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health && echo "✓" || echo "✗"
done
```

---

## Demo Checklist

**30 Minutes Before:**
- [ ] Boot Raspberry Pi / Start workstation
- [ ] Open terminal
- [ ] Start Docker services
- [ ] Run seed script
- [ ] Test all URLs
- [ ] Position browser windows
- [ ] Close unnecessary apps

**15 Minutes Before:**
- [ ] Re-test frontend
- [ ] Check Grafana dashboards loaded
- [ ] Open DEMO_SCRIPT.md for reference
- [ ] Print this cheat sheet
- [ ] Have backup screenshots ready
- [ ] Test screen sharing (if remote)

**5 Minutes Before:**
- [ ] Final service check (`docker ps`)
- [ ] Clear browser cache
- [ ] Reset timer
- [ ] Take deep breath
- [ ] Smile!

**During Demo:**
- [ ] Speak clearly and slowly
- [ ] Pause for questions
- [ ] Watch the time
- [ ] Stay calm if errors occur
- [ ] Use backup plan if needed

**After Demo:**
- [ ] Thank the audience
- [ ] Share GitHub link
- [ ] Collect feedback
- [ ] Answer questions thoroughly
- [ ] Follow up on action items

---

## Emergency Contacts

**If demo computer fails:**
- Backup laptop ready?
- Cloud deployment URL?
- Video recording backup?

**If internet fails (remote demo):**
- Phone hotspot ready?
- Pre-recorded video?
- Reschedule option?

---

## Confidence Boosters

- You built this entire system ✅
- All tests pass ✅
- Demo has been rehearsed 3+ times ✅
- Backup plans are ready ✅
- You know this better than anyone ✅

**You've got this! 🚀**
