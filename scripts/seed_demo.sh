#!/bin/bash
#
# Pulse ERP - Seed Demo Data Script
#
# Wrapper script to run seed_demo.py with proper environment
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Pulse ERP - Seed Demo Data"
echo "=========================================="
echo ""

# Check if services are running
echo "Checking services..."

if ! curl -s http://localhost/orders/health > /dev/null 2>&1; then
    echo "ERROR: Orders service not reachable at http://localhost/orders/health"
    echo "Please ensure services are running:"
    echo "  docker-compose -f docker-compose.base.yml -f docker-compose.services.yml up -d"
    exit 1
fi

if ! curl -s http://localhost/inventory/health > /dev/null 2>&1; then
    echo "ERROR: Inventory service not reachable at http://localhost/inventory/health"
    echo "Please ensure services are running"
    exit 1
fi

echo "✓ Services are running"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
echo "Using Python $PYTHON_VERSION"
echo ""

# Install requests if needed
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing Python requests library..."
    pip3 install requests
    echo ""
fi

# Run seed script
echo "Running seed data script..."
echo ""

export API_BASE_URL=${API_BASE_URL:-http://localhost}
export INVENTORY_API_URL=${INVENTORY_API_URL:-http://localhost}

python3 "$SCRIPT_DIR/seed_demo.py" "$@"
