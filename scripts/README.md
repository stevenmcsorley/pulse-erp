# Pulse ERP - Scripts

Utility scripts for database management, deployment, and demo data generation.

## Available Scripts

### seed_demo.sh / seed_demo.py

Generate demo data for the Pulse ERP system.

**Purpose:** Populate the system with realistic test data for demonstrations and development.

**What it creates:**
- 3 customers (ACME-CORP, TECHSTART-INC, RETAIL-PLUS)
- 5 products with initial inventory:
  - CAM-1001: 4K Security Camera ($299.99, 50 units)
  - CAM-2002: PTZ Dome Camera ($599.99, 30 units)
  - TRI-300: Professional Tripod ($89.99, 100 units)
  - BAT-150: Rechargeable Battery Pack ($49.99, 200 units)
  - CABLE-01: HDMI Cable 6ft ($12.99, 500 units)
- 10 sample orders with various combinations
- Auto-generated invoices (via billing service)

**Prerequisites:**
- Services running (orders, inventory, billing)
- Python 3.8+ installed
- `requests` library (auto-installed if missing)

**Usage:**

```bash
# Basic usage
./scripts/seed_demo.sh

# Or run Python directly
python3 scripts/seed_demo.py
```

**Environment Variables:**

```bash
# Optional - defaults shown
export API_BASE_URL=http://localhost:8001
export INVENTORY_API_URL=http://localhost:8002

./scripts/seed_demo.sh
```

**Output Example:**

```
==========================================
Pulse ERP - Demo Data Seed Script
==========================================
API Base URL: http://localhost:8001
Inventory API URL: http://localhost:8002

[12:34:56] Creating products...
[12:34:56]   ✓ Created product: CAM-1001 - 4K Security Camera
[12:34:56]     → Set stock: 50 units
[12:34:57]   ✓ Created product: CAM-2002 - PTZ Dome Camera
[12:34:57]     → Set stock: 30 units
[12:34:58]   ✓ Created product: TRI-300 - Professional Tripod
...

[12:35:01] Creating 10 orders...
[12:35:02]   ✓ Order 1/10: a7f3b2c1... ($1,799.95)
[12:35:02]     → Order placed successfully
[12:35:03]   ✓ Order 2/10: d4e8f1a9... ($1,291.96)
...

[12:35:15] Verifying seeded data...
[12:35:15]   ✓ Products in system: 5
[12:35:15]   ✓ Inventory items: 5
[12:35:15]     → Total stock: 880 units
[12:35:15]     → Reserved: 87 units
[12:35:16]   ✓ Orders in system: 10
[12:35:16]     → Status breakdown: {'placed': 10}
[12:35:16]     → Total revenue: $12,456.78

==========================================
Seed data generation complete in 19.34 seconds
==========================================

Next steps:
  1. Open frontend: http://localhost:3001
  2. View dashboards: http://localhost:3001/dashboards
  3. Check Grafana: http://localhost:3000
```

**Features:**

- **Idempotent:** Can be run multiple times safely
- **Fast:** Completes in <30 seconds
- **Realistic:** Generates varied order patterns
- **Verified:** Confirms data creation
- **Informative:** Detailed logging with timestamps

**Troubleshooting:**

If the script fails:

1. **Check services are running:**
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   ```

2. **Check Docker containers:**
   ```bash
   docker ps | grep pulse
   ```

3. **View service logs:**
   ```bash
   docker logs pulse-orders
   docker logs pulse-inventory
   ```

4. **Reset database (if needed):**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ./scripts/migrate.sh
   ./scripts/seed_demo.sh
   ```

## Other Scripts

### migrate.sh

Run database migrations (to be created).

### init-duckdb.sh

Initialize DuckDB OLAP schema (to be created).

### backup.sh

Backup PostgreSQL and DuckDB data (to be created).

### restore.sh

Restore from backup (to be created).

## Script Development

When creating new scripts:

1. **Make executable:** `chmod +x scripts/your_script.sh`
2. **Add shebang:** `#!/bin/bash` or `#!/usr/bin/env python3`
3. **Use set -e:** Exit on error in bash scripts
4. **Document here:** Add to this README
5. **Handle errors:** Provide helpful error messages
6. **Support --help:** Document command-line options
