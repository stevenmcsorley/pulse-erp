#!/bin/bash
#
# Pulse ERP - Database Migration Runner
# Applies SQL migrations to PostgreSQL database
#
# Usage: ./migrations/migrate.sh [up|down|status]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-pulse_erp}"
DB_USER="${POSTGRES_USER:-pulseadmin}"
DB_PASSWORD="${POSTGRES_PASSWORD:-changeme}"

# Migration directory
MIGRATIONS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PostgreSQL connection string
export PGPASSWORD="$DB_PASSWORD"
PSQL_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -v ON_ERROR_STOP=1"

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Pulse ERP - Database Migrations    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# Create migrations tracking table if it doesn't exist
create_migrations_table() {
    echo -e "${YELLOW}Creating migrations tracking table...${NC}"
    $PSQL_CMD <<-EOSQL
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            description TEXT
        );
EOSQL
    echo -e "${GREEN}✓ Migrations table ready${NC}"
}

# Check if migration has been applied
is_migration_applied() {
    local version=$1
    local count=$($PSQL_CMD -t -c "SELECT COUNT(*) FROM schema_migrations WHERE version = '$version';")
    [ "$count" -gt 0 ]
}

# Apply a single migration
apply_migration() {
    local file=$1
    local version=$(basename "$file" .sql)

    if is_migration_applied "$version"; then
        echo -e "${YELLOW}⊘ $version already applied, skipping${NC}"
        return 0
    fi

    echo -e "${BLUE}→ Applying migration: $version${NC}"

    # Apply the migration
    if $PSQL_CMD -f "$file"; then
        # Record successful migration
        $PSQL_CMD <<-EOSQL
            INSERT INTO schema_migrations (version, description)
            VALUES ('$version', 'Applied from $file');
EOSQL
        echo -e "${GREEN}✓ $version applied successfully${NC}"
    else
        echo -e "${RED}✗ Failed to apply $version${NC}"
        return 1
    fi
}

# Rollback a migration
rollback_migration() {
    local version=$1
    local rollback_file="${MIGRATIONS_DIR}/${version}_rollback.sql"

    if [ ! -f "$rollback_file" ]; then
        echo -e "${RED}✗ Rollback file not found: $rollback_file${NC}"
        return 1
    fi

    echo -e "${YELLOW}↓ Rolling back migration: $version${NC}"

    if $PSQL_CMD -f "$rollback_file"; then
        # Remove from migrations table
        $PSQL_CMD <<-EOSQL
            DELETE FROM schema_migrations WHERE version = '$version';
EOSQL
        echo -e "${GREEN}✓ $version rolled back successfully${NC}"
    else
        echo -e "${RED}✗ Failed to rollback $version${NC}"
        return 1
    fi
}

# Show migration status
show_status() {
    echo -e "${BLUE}Migration Status:${NC}"
    echo ""

    # List all migration files
    for file in "$MIGRATIONS_DIR"/*.sql; do
        if [[ "$file" == *"_rollback.sql" ]]; then
            continue
        fi

        local version=$(basename "$file" .sql)

        if is_migration_applied "$version"; then
            local applied_at=$($PSQL_CMD -t -c "SELECT applied_at FROM schema_migrations WHERE version = '$version';")
            echo -e "${GREEN}✓${NC} $version (applied: $applied_at)"
        else
            echo -e "${YELLOW}○${NC} $version (pending)"
        fi
    done

    echo ""

    # Show applied migrations from database
    echo -e "${BLUE}Applied Migrations:${NC}"
    $PSQL_CMD -c "SELECT version, applied_at FROM schema_migrations ORDER BY applied_at;"
}

# Main migration command
migrate_up() {
    echo -e "${GREEN}Running migrations...${NC}"
    echo ""

    create_migrations_table

    # Apply all pending migrations in order
    for file in "$MIGRATIONS_DIR"/*.sql; do
        if [[ "$file" == *"_rollback.sql" ]]; then
            continue
        fi

        apply_migration "$file"
    done

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  All migrations completed!           ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
}

# Rollback last migration
migrate_down() {
    echo -e "${YELLOW}Rolling back last migration...${NC}"
    echo ""

    # Get last applied migration
    local last_migration=$($PSQL_CMD -t -c "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1;")

    if [ -z "$last_migration" ]; then
        echo -e "${YELLOW}No migrations to rollback${NC}"
        return 0
    fi

    rollback_migration "$last_migration"

    echo ""
    echo -e "${GREEN}Rollback completed!${NC}"
}

# Test database connection
test_connection() {
    echo -e "${YELLOW}Testing database connection...${NC}"
    if $PSQL_CMD -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
        echo -e "  Host: $DB_HOST:$DB_PORT"
        echo -e "  Database: $DB_NAME"
        echo -e "  User: $DB_USER"
        return 0
    else
        echo -e "${RED}✗ Database connection failed${NC}"
        echo -e "  Host: $DB_HOST:$DB_PORT"
        echo -e "  Database: $DB_NAME"
        echo -e "  User: $DB_USER"
        return 1
    fi
}

# Parse command
COMMAND="${1:-up}"

case "$COMMAND" in
    up)
        test_connection && migrate_up
        ;;
    down)
        test_connection && migrate_down
        ;;
    status)
        test_connection && show_status
        ;;
    test)
        test_connection
        ;;
    *)
        echo "Usage: $0 [up|down|status|test]"
        echo ""
        echo "Commands:"
        echo "  up      - Apply all pending migrations (default)"
        echo "  down    - Rollback the last migration"
        echo "  status  - Show migration status"
        echo "  test    - Test database connection"
        exit 1
        ;;
esac
