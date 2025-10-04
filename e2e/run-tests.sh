#!/bin/bash
#
# Pulse ERP - E2E Test Runner
#
# Runs Playwright E2E tests with proper setup
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Pulse ERP - E2E Test Runner"
echo "=========================================="
echo ""

# Check if frontend is running
echo "Checking frontend..."
if ! curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo "WARNING: Frontend not reachable at http://localhost:3001"
    echo "Starting frontend in background..."
    cd "$SCRIPT_DIR/../frontend" && npm run dev > /dev/null 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend PID: $FRONTEND_PID"
    sleep 5
fi

# Check services
echo "Checking services..."
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "ERROR: Orders service not reachable"
    exit 1
fi

if ! curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "ERROR: Inventory service not reachable"
    exit 1
fi

echo "✓ Services are running"
echo ""

# Install dependencies if needed
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    echo "Installing dependencies..."
    cd "$SCRIPT_DIR"
    npm install
    npx playwright install --with-deps chromium
    echo ""
fi

# Run tests
echo "Running E2E tests..."
echo ""

cd "$SCRIPT_DIR"

# Set environment variables
export BASE_URL=${BASE_URL:-http://localhost:3001}
export API_BASE_URL=${API_BASE_URL:-http://localhost:8001}
export INVENTORY_API_URL=${INVENTORY_API_URL:-http://localhost:8002}
export OLAP_API_URL=${OLAP_API_URL:-http://localhost:8004}

# Run tests
npm test

TEST_EXIT_CODE=$?

# Cleanup
if [ -n "$FRONTEND_PID" ]; then
    echo ""
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
fi

exit $TEST_EXIT_CODE
