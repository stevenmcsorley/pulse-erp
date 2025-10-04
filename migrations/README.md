# Database Migrations

This directory contains SQL migration scripts for the Pulse ERP database schema.

## Quick Start

```bash
# Apply all migrations
./migrations/migrate.sh up

# Check migration status
./migrations/migrate.sh status

# Rollback last migration
./migrations/migrate.sh down

# Test database connection
./migrations/migrate.sh test
```

## Migration Files

Migrations are numbered sequentially and must be prefixed with a three-digit number:

- `001_initial_schema.sql` - Initial database schema (all core tables)
- `001_initial_schema_rollback.sql` - Rollback script for initial schema
- Future migrations: `002_add_feature.sql`, `003_alter_table.sql`, etc.

## Database Schema

### Core Tables

**Customers**
- Master customer data
- Email uniqueness enforced
- Supports metadata (JSONB)

**Products**
- Product catalog with pricing
- SKU as primary key
- Price validation (>= 0)

**Inventory Items**
- Stock levels per SKU
- Reserved quantity tracking
- Reorder point alerts
- Constraint: reserved_qty <= qty_on_hand

**Orders**
- Customer orders with status tracking
- Status: draft, placed, cancelled, shipped, completed
- Links to customer and order items

**Order Items**
- Line items for each order
- References products by SKU
- Price snapshot at time of order

**Invoices**
- Generated from orders
- Status: issued, paid, overdue, cancelled
- Due date tracking
- Payment timestamp

**Ledger Entries**
- Double-entry accounting
- Debit/credit validation
- Reference type: order, invoice, payment, payroll, adjustment
- Append-only (no updates/deletes)

**Employees**
- HR master data
- Salary stored in pence (integer)
- Payroll metadata (JSONB)
- Active/inactive flag

**Events Log**
- Domain events audit trail
- Append-only event store
- JSONB payload for flexibility

### Views

**order_details**
- Orders with customer and items (JSON aggregated)

**inventory_status**
- Current stock levels with reorder flags
- Available quantity (qty_on_hand - reserved_qty)

**invoice_details**
- Invoices with customer info and aging calculation

**account_balances**
- Account balances from ledger entries

### Triggers

**update_updated_at_column**
- Automatically updates `updated_at` timestamp on row modification
- Applied to: customers, products, inventory_items, orders, invoices, employees

## Environment Variables

The migration script uses these environment variables (from `.env` or environment):

```bash
DB_HOST=localhost          # Database host
DB_PORT=5432               # Database port
POSTGRES_DB=pulse_erp      # Database name
POSTGRES_USER=pulseadmin   # Database user
POSTGRES_PASSWORD=changeme # Database password
```

## Migration Workflow

### Creating a New Migration

1. Create migration file: `migrations/00X_description.sql`
2. Create rollback file: `migrations/00X_description_rollback.sql`
3. Test migration locally:
   ```bash
   ./migrations/migrate.sh up
   ./migrations/migrate.sh status
   ```
4. Test rollback:
   ```bash
   ./migrations/migrate.sh down
   ./migrations/migrate.sh status
   ```
5. Commit both files to version control

### Migration Best Practices

- **Idempotent**: Use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
- **Reversible**: Always provide rollback scripts
- **Tested**: Test both up and down migrations
- **Atomic**: Each migration should be a logical unit
- **Data-safe**: Use `ALTER TABLE` carefully, avoid data loss
- **Constraints**: Add constraints after data is clean
- **Indexes**: Add indexes last in large tables

### Common Operations

**Add a column:**
```sql
ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(50);
```

**Add an index:**
```sql
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
```

**Add a constraint:**
```sql
ALTER TABLE products ADD CONSTRAINT check_price_positive CHECK (price > 0);
```

**Rollback:**
```sql
ALTER TABLE products DROP COLUMN IF EXISTS category;
DROP INDEX IF EXISTS idx_products_category;
ALTER TABLE products DROP CONSTRAINT IF EXISTS check_price_positive;
```

## Troubleshooting

### Connection Failed

```bash
# Check if Postgres is running
docker compose ps postgres

# Check connection manually
psql -h localhost -U pulseadmin -d pulse_erp

# View Postgres logs
docker compose logs postgres
```

### Migration Failed Mid-Way

Postgres transactions ensure atomicity. If a migration fails:
1. The entire migration is rolled back automatically
2. Fix the SQL error
3. Re-run `./migrations/migrate.sh up`

### Reset Database (Development Only)

```bash
# Drop all tables and start fresh
docker compose down -v  # Removes volumes
docker compose up -d postgres
./migrations/migrate.sh up
```

### Check Applied Migrations

```bash
# Using migrate script
./migrations/migrate.sh status

# Direct SQL query
psql -h localhost -U pulseadmin -d pulse_erp -c "SELECT * FROM schema_migrations ORDER BY applied_at;"
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Test migration on staging database
- [ ] Review rollback script
- [ ] Backup database before migration
- [ ] Schedule migration during maintenance window
- [ ] Monitor application logs during migration

### Running Migrations in Production

```bash
# Backup first
docker exec pulse-postgres pg_dump -U pulseadmin pulse_erp > backup_pre_migration.sql

# Apply migration
./migrations/migrate.sh up

# Verify
./migrations/migrate.sh status

# If issues, rollback
./migrations/migrate.sh down

# Restore from backup if needed
docker exec -i pulse-postgres psql -U pulseadmin pulse_erp < backup_pre_migration.sql
```

## Schema Versioning

The `schema_migrations` table tracks applied migrations:

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT
);
```

This ensures migrations are applied exactly once and provides audit trail.

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Migration Best Practices](https://www.liquibase.org/get-started/best-practices)
- Data Model: `/docs/DATA_MODEL.md`
