#!/bin/bash

#
# DuckDB Migration Script
# Usage: ./migrate.sh [up|down|status]
#

set -e

DUCKDB_PATH="${DUCKDB_PATH:-/data/pulse_olap.duckdb}"
MIGRATIONS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if DuckDB CLI is available
if ! command -v duckdb &> /dev/null; then
    echo -e "${RED}Error: duckdb CLI not found${NC}"
    echo "Install with: pip install duckdb"
    exit 1
fi

# Function to run migration up
migrate_up() {
    echo -e "${GREEN}Running DuckDB migrations...${NC}"

    for migration in "$MIGRATIONS_DIR"/*_initial_olap_schema.sql; do
        if [ -f "$migration" ]; then
            echo -e "${YELLOW}Applying: $(basename "$migration")${NC}"
            duckdb "$DUCKDB_PATH" < "$migration"
            echo -e "${GREEN}✓ Applied: $(basename "$migration")${NC}"
        fi
    done

    echo -e "${GREEN}✓ All migrations completed${NC}"
}

# Function to run migration down (rollback)
migrate_down() {
    echo -e "${YELLOW}Rolling back DuckDB migrations...${NC}"

    for rollback in "$MIGRATIONS_DIR"/*_rollback.sql; do
        if [ -f "$rollback" ]; then
            echo -e "${YELLOW}Rolling back: $(basename "$rollback")${NC}"
            duckdb "$DUCKDB_PATH" < "$rollback"
            echo -e "${GREEN}✓ Rolled back: $(basename "$rollback")${NC}"
        fi
    done

    echo -e "${GREEN}✓ Rollback completed${NC}"
}

# Function to check migration status
migration_status() {
    echo -e "${GREEN}DuckDB Migration Status${NC}"
    echo "Database: $DUCKDB_PATH"
    echo ""

    if [ ! -f "$DUCKDB_PATH" ]; then
        echo -e "${YELLOW}Database file does not exist${NC}"
        exit 0
    fi

    echo "Schema version:"
    duckdb "$DUCKDB_PATH" "SELECT * FROM schema_version ORDER BY version DESC LIMIT 1" 2>/dev/null || echo "No migrations applied"

    echo ""
    echo "Table counts:"
    duckdb "$DUCKDB_PATH" "
        SELECT 'sales_by_hour' AS table_name, COUNT(*) AS row_count FROM sales_by_hour
        UNION ALL
        SELECT 'stock_snapshot', COUNT(*) FROM stock_snapshot
        UNION ALL
        SELECT 'ar_aging', COUNT(*) FROM ar_aging
        UNION ALL
        SELECT 'order_events', COUNT(*) FROM order_events
        UNION ALL
        SELECT 'invoice_events', COUNT(*) FROM invoice_events
        UNION ALL
        SELECT 'stock_events', COUNT(*) FROM stock_events
    " 2>/dev/null || echo "Tables not created yet"
}

# Main command router
case "${1:-}" in
    up)
        migrate_up
        ;;
    down)
        migrate_down
        ;;
    status)
        migration_status
        ;;
    *)
        echo "Usage: $0 {up|down|status}"
        echo ""
        echo "Commands:"
        echo "  up      - Apply migrations"
        echo "  down    - Rollback migrations"
        echo "  status  - Show migration status"
        exit 1
        ;;
esac
