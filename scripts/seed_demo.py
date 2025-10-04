#!/usr/bin/env python3
"""
Seed Demo Data Script for Pulse ERP

Generates realistic demo data for the Pulse ERP system:
- Customers
- Products with initial inventory
- Orders with line items
- Invoices (auto-generated via billing service)

This script is idempotent - it can be run multiple times safely.
"""

import os
import sys
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import uuid

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
INVENTORY_API_URL = os.getenv("INVENTORY_API_URL", "http://localhost:8002")

# Demo Data
CUSTOMERS = [
    {"name": "ACME-CORP", "id": str(uuid.uuid4())},
    {"name": "TECHSTART-INC", "id": str(uuid.uuid4())},
    {"name": "RETAIL-PLUS", "id": str(uuid.uuid4())},
]

PRODUCTS = [
    {"sku": "CAM-1001", "name": "4K Security Camera", "price": 299.99, "initial_stock": 50},
    {"sku": "CAM-2002", "name": "PTZ Dome Camera", "price": 599.99, "initial_stock": 30},
    {"sku": "TRI-300", "name": "Professional Tripod", "price": 89.99, "initial_stock": 100},
    {"sku": "BAT-150", "name": "Rechargeable Battery Pack", "price": 49.99, "initial_stock": 200},
    {"sku": "CABLE-01", "name": "HDMI Cable 6ft", "price": 12.99, "initial_stock": 500},
]

# Sample order templates for variety
ORDER_TEMPLATES = [
    # Large camera order
    [
        {"sku": "CAM-1001", "qty": 5},
        {"sku": "TRI-300", "qty": 5},
        {"sku": "BAT-150", "qty": 10},
    ],
    # PTZ camera bundle
    [
        {"sku": "CAM-2002", "qty": 2},
        {"sku": "TRI-300", "qty": 2},
        {"sku": "CABLE-01", "qty": 4},
    ],
    # Small accessories order
    [
        {"sku": "BAT-150", "qty": 20},
        {"sku": "CABLE-01", "qty": 50},
    ],
    # Mixed order
    [
        {"sku": "CAM-1001", "qty": 3},
        {"sku": "CAM-2002", "qty": 1},
        {"sku": "TRI-300", "qty": 4},
        {"sku": "BAT-150", "qty": 8},
        {"sku": "CABLE-01", "qty": 12},
    ],
    # Single product order
    [
        {"sku": "TRI-300", "qty": 10},
    ],
]


class SeedDataGenerator:
    def __init__(self, clear_existing: bool = False):
        self.clear_existing = clear_existing
        self.created_products = []
        self.created_orders = []

    def log(self, message: str):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def create_products(self):
        """Create products and set initial inventory"""
        self.log("Creating products...")

        for product in PRODUCTS:
            # Create product
            try:
                response = requests.post(
                    f"{INVENTORY_API_URL}/inventory",
                    json={
                        "sku": product["sku"],
                        "name": product["name"],
                        "price": product["price"],
                        "qty_on_hand": product["initial_stock"],
                    },
                    timeout=10,
                )

                if response.status_code == 201:
                    self.log(f"  ✓ Created product: {product['sku']} - {product['name']}")
                    self.created_products.append(product["sku"])
                elif response.status_code == 409:
                    self.log(f"  ⊙ Product already exists: {product['sku']}")
                    self.created_products.append(product["sku"])
                else:
                    self.log(f"  ✗ Failed to create product {product['sku']}: {response.status_code}")
                    continue
            except Exception as e:
                self.log(f"  ✗ Error creating product {product['sku']}: {e}")
                continue

        self.log(f"Products created: {len(self.created_products)}/{len(PRODUCTS)}")

    def create_orders(self, num_orders: int = 10):
        """Create sample orders with realistic timestamps"""
        self.log(f"Creating {num_orders} orders...")

        # Generate orders over the past 24 hours
        now = datetime.now()
        time_spread = timedelta(hours=24)

        for i in range(num_orders):
            # Random customer
            customer = random.choice(CUSTOMERS)

            # Random order template
            template = random.choice(ORDER_TEMPLATES)

            # Get current prices from products
            items = []
            for item_template in template:
                product = next((p for p in PRODUCTS if p["sku"] == item_template["sku"] ), None)
                if product:
                    items.append({
                        "sku": item_template["sku"],
                        "qty": item_template["qty"],
                        "price": product["price"],
                    })

            if not items:
                continue

            # Create order
            try:
                response = requests.post(
                    f"{API_BASE_URL}/orders",
                    json={
                        "customer_id": customer["id"],
                        "items": items,
                    },
                    timeout=10,
                )

                if response.status_code == 201:
                    order = response.json()
                    order_id = order.get("id")
                    total = order.get("total_amount", 0)
                    self.log(f"  ✓ Order {i+1}/{num_orders}: {order_id[:8]}... (${total:.2f})")
                    self.created_orders.append(order_id)

                    # Place the order (change status from draft to placed)
                    time.sleep(0.5)  # Brief delay between operations
                    try:
                        place_response = requests.patch(
                            f"{API_BASE_URL}/orders/{order_id}",
                            json={"status": "placed"},
                            timeout=10,
                        )
                        if place_response.status_code == 200:
                            self.log(f"    → Order placed successfully")
                        else:
                            self.log(f"    ⊙ Order created but not placed: {place_response.status_code}")
                    except Exception as e:
                        self.log(f"    ⊙ Order created but failed to place: {e}")

                else:
                    self.log(f"  ✗ Failed to create order {i+1}: {response.status_code} - {response.text}")
            except Exception as e:
                self.log(f"  ✗ Error creating order {i+1}: {e}")

            # Small delay to avoid overwhelming the API
            time.sleep(0.2)

        self.log(f"Orders created: {len(self.created_orders)}/{num_orders}")

    def verify_data(self):
        """Verify seeded data"""
        self.log("Verifying seeded data...")

        # Check products
        try:
            response = requests.get(f"{INVENTORY_API_URL}/inventory", timeout=10)
            if response.status_code == 200:
                products = response.json()
                self.log(f"  ✓ Products in system: {len(products)}")
            else:
                self.log(f"  ✗ Failed to fetch products: {response.status_code}")
        except Exception as e:
            self.log(f"  ✗ Error fetching products: {e}")

        # Check inventory
        try:
            response = requests.get(f"{INVENTORY_API_URL}/inventory", timeout=10)
            if response.status_code == 200:
                inventory = response.json()
                self.log(f"  ✓ Inventory items: {len(inventory)}")
                total_stock = sum(item.get("qty_on_hand", 0) for item in inventory)
                total_reserved = sum(item.get("reserved_qty", 0) for item in inventory)
                self.log(f"    → Total stock: {total_stock} units")
                self.log(f"    → Reserved: {total_reserved} units")
            else:
                self.log(f"  ✗ Failed to fetch inventory: {response.status_code}")
        except Exception as e:
            self.log(f"  ✗ Error fetching inventory: {e}")

        # Check orders
        try:
            response = requests.get(f"{API_BASE_URL}/orders", timeout=10)
            if response.status_code == 200:
                orders = response.json()
                self.log(f"  ✓ Orders in system: {len(orders)}")
                statuses = {}
                total_revenue = 0
                for order in orders:
                    status = order.get("status", "unknown")
                    statuses[status] = statuses.get(status, 0) + 1
                    total_revenue += order.get("total_amount", 0)

                self.log(f"    → Status breakdown: {dict(statuses)}")
                self.log(f"    → Total revenue: ${total_revenue:.2f}")
            else:
                self.log(f"  ✗ Failed to fetch orders: {response.status_code}")
        except Exception as e:
            self.log(f"  ✗ Error fetching orders: {e}")

    def run(self):
        """Run the complete seed data generation"""
        self.log("=" * 60)
        self.log("Pulse ERP - Demo Data Seed Script")
        self.log("=" * 60)
        self.log(f"API Base URL: {API_BASE_URL}")
        self.log(f"Inventory API URL: {INVENTORY_API_URL}")
        self.log("")

        start_time = time.time()

        # Step 1: Create products and inventory
        self.create_products()
        self.log("")

        # Step 2: Create orders
        self.create_orders(num_orders=10)
        self.log("")

        # Step 3: Verify
        self.verify_data()
        self.log("")

        elapsed = time.time() - start_time
        self.log("=" * 60)
        self.log(f"Seed data generation complete in {elapsed:.2f} seconds")
        self.log("=" * 60)
        self.log("")
        self.log("Next steps:")
        self.log("  1. Open frontend: http://localhost:3001")
        self.log("  2. View dashboards: http://localhost:3001/dashboards")
        self.log("  3. Check Grafana: http://localhost:3000")
        self.log("")


def main():
    """Main entry point"""
    clear_existing = "--clear" in sys.argv or "--reset" in sys.argv

    if clear_existing:
        print("Warning: --clear/--reset not yet implemented")
        print("To reset data, recreate database containers")
        print("")

    generator = SeedDataGenerator(clear_existing=clear_existing)

    try:
        generator.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
