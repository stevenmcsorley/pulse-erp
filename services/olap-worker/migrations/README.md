# DuckDB OLAP Schema Documentation

## Overview

The DuckDB OLAP schema provides analytical tables and views for real-time business intelligence in Pulse ERP. This schema is optimized for fast analytical queries while maintaining a small footprint suitable for Raspberry Pi 5.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           OLAP Worker (Event Consumer)              │
│  Consumes NATS events → Materializes to DuckDB      │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   DuckDB File     │
         │  pulse_olap.duckdb│
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐    ┌────▼────┐    ┌───▼───┐
│ Events│    │Aggregates│    │ Views │
│Tables │    │  Tables  │    │       │
└───────┘    └──────────┘    └───────┘
```

## Table Categories

### 1. Aggregate Tables (Pre-computed)

These tables store pre-aggregated data for fast dashboard queries:

#### `sales_by_hour`
Hourly sales metrics for trend analysis.

| Column | Type | Description |
|--------|------|-------------|
| hour | TIMESTAMP | Hour bucket (PK) |
| total_orders | INTEGER | Number of orders in this hour |
| total_revenue | DECIMAL(14,2) | Total revenue in this hour |
| avg_order_value | DECIMAL(14,2) | Average order value |
| unique_customers | INTEGER | Distinct customers |
| updated_at | TIMESTAMP | Last update timestamp |

**Indexes:** Primary key on `hour`

**Use Cases:**
- Sales dashboards
- Hourly trend charts
- Peak hour analysis

#### `stock_snapshot`
Current inventory levels for each SKU.

| Column | Type | Description |
|--------|------|-------------|
| sku | VARCHAR | Product SKU (PK) |
| product_name | VARCHAR | Product name |
| qty_on_hand | INTEGER | Physical quantity |
| reserved_qty | INTEGER | Quantity reserved for orders |
| available_qty | INTEGER | Available for sale |
| reorder_point | INTEGER | Reorder threshold |
| needs_reorder | BOOLEAN | Alert flag |
| last_updated | TIMESTAMP | Last update |

**Indexes:** Primary key on `sku`

**Use Cases:**
- Inventory dashboards
- Low stock alerts
- Reorder reports

#### `ar_aging`
Accounts receivable aging buckets by customer.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | UUID | Customer ID (PK) |
| customer_name | VARCHAR | Customer name |
| total_outstanding | DECIMAL(14,2) | Total AR |
| current_amount | DECIMAL(14,2) | Current (0-29 days) |
| days_30 | DECIMAL(14,2) | 30-59 days overdue |
| days_60 | DECIMAL(14,2) | 60-89 days overdue |
| days_90_plus | DECIMAL(14,2) | 90+ days overdue |
| oldest_invoice_date | DATE | Oldest unpaid invoice |
| updated_at | TIMESTAMP | Last update |

**Indexes:** Primary key on `customer_id`

**Use Cases:**
- Collections management
- Cash flow forecasting
- Customer credit analysis

---

### 2. Raw Event Tables (Event Sourcing)

These tables store all domain events for historical analysis and replay:

#### `order_events`
All order lifecycle events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| order_id | UUID | Order reference |
| event_type | VARCHAR | Event type (order_created, order_updated, etc.) |
| customer_id | UUID | Customer reference |
| total_amount | DECIMAL(14,2) | Order total |
| status | VARCHAR | Order status |
| event_timestamp | TIMESTAMP | When event occurred |
| processed_at | TIMESTAMP | When OLAP worker processed |

**Indexes:**
- `idx_order_events_order_id` - Fast lookups by order
- `idx_order_events_timestamp` - Time-range queries
- `idx_order_events_customer_id` - Customer analysis

**Use Cases:**
- Order history analysis
- Customer behavior tracking
- Event replay for debugging

#### `invoice_events`
All invoice lifecycle events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| invoice_id | UUID | Invoice reference |
| order_id | UUID | Related order |
| event_type | VARCHAR | Event type (invoice_created, payment_received, etc.) |
| amount | DECIMAL(14,2) | Invoice amount |
| status | VARCHAR | Invoice status |
| due_date | DATE | Payment due date |
| event_timestamp | TIMESTAMP | When event occurred |
| processed_at | TIMESTAMP | When processed |

**Indexes:**
- `idx_invoice_events_invoice_id` - Invoice lookups
- `idx_invoice_events_order_id` - Order correlation
- `idx_invoice_events_timestamp` - Time queries

**Use Cases:**
- Payment tracking
- Revenue recognition
- Aging calculations

#### `stock_events`
All inventory movement events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| event_type | VARCHAR | Event type (stock_reserved, reservation_failed, etc.) |
| sku | VARCHAR | Product SKU |
| order_id | UUID | Related order |
| qty_reserved | INTEGER | Quantity reserved |
| event_timestamp | TIMESTAMP | When event occurred |
| processed_at | TIMESTAMP | When processed |

**Indexes:**
- `idx_stock_events_sku` - Product analysis
- `idx_stock_events_order_id` - Order correlation
- `idx_stock_events_timestamp` - Time queries

**Use Cases:**
- Inventory turnover analysis
- Stockout tracking
- Demand forecasting

---

### 3. Analytical Views

Pre-defined views for common analytics queries:

#### `sales_summary_24h`
Last 24 hours of sales data.

```sql
SELECT * FROM sales_summary_24h;
```

#### `low_stock_items`
Items that need reordering.

```sql
SELECT * FROM low_stock_items;
```

#### `overdue_ar`
Customers with overdue invoices.

```sql
SELECT * FROM overdue_ar ORDER BY days_overdue DESC;
```

#### `daily_order_volume`
Daily order count and revenue.

```sql
SELECT * FROM daily_order_volume WHERE order_date >= CURRENT_DATE - 30;
```

#### `stock_movement_summary`
Stock reservation summary by SKU.

```sql
SELECT * FROM stock_movement_summary LIMIT 10;
```

---

## Migration Management

### Running Migrations

```bash
# Apply all migrations
./migrations/migrate.sh up

# Check migration status
./migrations/migrate.sh status

# Rollback all migrations
./migrations/migrate.sh down
```

### Environment Variables

- `DUCKDB_PATH` - Path to DuckDB file (default: `/data/pulse_olap.duckdb`)

### Migration Files

- `001_initial_olap_schema.sql` - Creates all tables, indexes, views, and seed data
- `001_initial_olap_schema_rollback.sql` - Drops all objects
- `migrate.sh` - Migration runner script

---

## Query Performance

### Optimization Tips

1. **Use indexed columns** in WHERE clauses:
   ```sql
   -- Fast (uses index)
   SELECT * FROM order_events WHERE order_id = '...';

   -- Slow (no index)
   SELECT * FROM order_events WHERE status = 'completed';
   ```

2. **Pre-aggregate when possible** - Use aggregate tables instead of raw events:
   ```sql
   -- Fast
   SELECT * FROM sales_by_hour WHERE hour >= CURRENT_TIMESTAMP - INTERVAL '7 days';

   -- Slower
   SELECT DATE_TRUNC('hour', event_timestamp), SUM(total_amount)
   FROM order_events
   WHERE event_type = 'order_created'
   GROUP BY DATE_TRUNC('hour', event_timestamp);
   ```

3. **Limit result sets** - Always use LIMIT for exploratory queries:
   ```sql
   SELECT * FROM order_events ORDER BY event_timestamp DESC LIMIT 100;
   ```

### Expected Performance

On Raspberry Pi 5 (8GB RAM):
- **Aggregate queries:** <50ms for pre-computed tables
- **Event queries:** <200ms for time-range scans (1M events)
- **Complex joins:** <500ms for multi-table analytics

---

## Seed Data

The initial migration includes sample data for testing:

- 3 hours of sales data
- 3 sample products with inventory levels
- 2 customer AR aging records

**To reset seed data:**

```bash
./migrations/migrate.sh down
./migrations/migrate.sh up
```

---

## Schema Versioning

The `schema_version` table tracks applied migrations:

```sql
SELECT * FROM schema_version ORDER BY version DESC;
```

| version | applied_at | description |
|---------|------------|-------------|
| 1 | 2025-10-04 ... | Initial OLAP schema with aggregate and event tables |

---

## Integration with OLAP Worker

The OLAP Worker (`services/olap-worker`) automatically initializes this schema on startup via `app/duckdb_client.py`. The migration files provide:

1. **Documentation** - Schema reference
2. **CLI Management** - Manual schema operations
3. **Rollback Capability** - Safe schema changes
4. **Version Control** - Track schema evolution

---

## DuckDB CLI Usage

```bash
# Open database
duckdb /data/pulse_olap.duckdb

# List tables
.tables

# Describe table
DESCRIBE sales_by_hour;

# Query data
SELECT * FROM sales_summary_24h;

# Export to CSV
COPY (SELECT * FROM daily_order_volume) TO 'daily_sales.csv' (HEADER, DELIMITER ',');

# Exit
.quit
```

---

## Backup and Restore

### Backup

```bash
# Copy DuckDB file
cp /data/pulse_olap.duckdb /backups/pulse_olap_$(date +%Y%m%d).duckdb
```

### Restore

```bash
# Stop OLAP worker first
docker stop pulse-olap-worker

# Restore file
cp /backups/pulse_olap_20251004.duckdb /data/pulse_olap.duckdb

# Restart worker
docker start pulse-olap-worker
```

---

## Future Enhancements

Planned for Sprint 2:

- [ ] Partitioning for large event tables (by month)
- [ ] Materialized aggregate refresh scheduling
- [ ] Additional views for profit margin analysis
- [ ] Data retention policies (archive old events)
- [ ] DuckDB Python API for advanced analytics
