"""DuckDB Client for OLAP Worker"""
import os
import duckdb
from typing import Optional
from datetime import datetime


class DuckDBClient:
    """DuckDB connection manager for OLAP tables"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("DUCKDB_PATH", "/data/pulse_olap.duckdb")
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self):
        """Establish connection to DuckDB"""
        self.conn = duckdb.connect(self.db_path)
        print(f"Connected to DuckDB at {self.db_path}")
        self._initialize_schema()

    def close(self):
        """Close DuckDB connection"""
        if self.conn:
            self.conn.close()
            print("DuckDB connection closed")

    def _initialize_schema(self):
        """Create OLAP tables if they don't exist"""
        # Sales by hour aggregate
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_by_hour (
                hour TIMESTAMP PRIMARY KEY,
                total_orders INTEGER DEFAULT 0,
                total_revenue DECIMAL(14,2) DEFAULT 0,
                avg_order_value DECIMAL(14,2) DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Stock snapshot (point-in-time inventory levels)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_snapshot (
                sku VARCHAR PRIMARY KEY,
                product_name VARCHAR,
                qty_on_hand INTEGER DEFAULT 0,
                reserved_qty INTEGER DEFAULT 0,
                available_qty INTEGER DEFAULT 0,
                reorder_point INTEGER DEFAULT 0,
                needs_reorder BOOLEAN DEFAULT FALSE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # AR aging (accounts receivable aging)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ar_aging (
                customer_id UUID PRIMARY KEY,
                customer_name VARCHAR,
                total_outstanding DECIMAL(14,2) DEFAULT 0,
                current_amount DECIMAL(14,2) DEFAULT 0,
                days_30 DECIMAL(14,2) DEFAULT 0,
                days_60 DECIMAL(14,2) DEFAULT 0,
                days_90_plus DECIMAL(14,2) DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Order events log (raw events for analysis)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS order_events (
                id INTEGER PRIMARY KEY DEFAULT nextval('order_events_seq'),
                order_id UUID NOT NULL,
                event_type VARCHAR NOT NULL,
                customer_id UUID,
                total_amount DECIMAL(14,2),
                status VARCHAR,
                event_timestamp TIMESTAMP NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sequence for order_events
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS order_events_seq START 1
        """)

        # Invoice events log
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_events (
                id INTEGER PRIMARY KEY DEFAULT nextval('invoice_events_seq'),
                invoice_id UUID NOT NULL,
                order_id UUID,
                event_type VARCHAR NOT NULL,
                amount DECIMAL(14,2),
                status VARCHAR,
                due_date DATE,
                event_timestamp TIMESTAMP NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS invoice_events_seq START 1
        """)

        # Stock events log
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_events (
                id INTEGER PRIMARY KEY DEFAULT nextval('stock_events_seq'),
                event_type VARCHAR NOT NULL,
                sku VARCHAR NOT NULL,
                order_id UUID,
                qty_reserved INTEGER,
                event_timestamp TIMESTAMP NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS stock_events_seq START 1
        """)

        print("DuckDB schema initialized")

    def upsert_sales_by_hour(self, hour: datetime, total_orders: int, total_revenue: float):
        """Update sales aggregate for a given hour"""
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # DuckDB doesn't have native UPSERT, so we use INSERT OR REPLACE
        self.conn.execute("""
            INSERT OR REPLACE INTO sales_by_hour (hour, total_orders, total_revenue, avg_order_value, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, [hour, total_orders, total_revenue, avg_order_value])

    def upsert_stock_snapshot(self, sku: str, product_name: str, qty_on_hand: int,
                              reserved_qty: int, reorder_point: int = 10):
        """Update stock snapshot for a SKU"""
        available_qty = qty_on_hand - reserved_qty
        needs_reorder = available_qty <= reorder_point

        self.conn.execute("""
            INSERT OR REPLACE INTO stock_snapshot
            (sku, product_name, qty_on_hand, reserved_qty, available_qty, reorder_point, needs_reorder, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, [sku, product_name, qty_on_hand, reserved_qty, available_qty, reorder_point, needs_reorder])

    def insert_order_event(self, order_id: str, event_type: str, customer_id: str,
                          total_amount: float, status: str, event_timestamp: datetime):
        """Insert raw order event"""
        self.conn.execute("""
            INSERT INTO order_events (order_id, event_type, customer_id, total_amount, status, event_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [order_id, event_type, customer_id, total_amount, status, event_timestamp])

    def insert_invoice_event(self, invoice_id: str, order_id: str, event_type: str,
                            amount: float, status: str, due_date: str, event_timestamp: datetime):
        """Insert raw invoice event"""
        self.conn.execute("""
            INSERT INTO invoice_events (invoice_id, order_id, event_type, amount, status, due_date, event_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [invoice_id, order_id, event_type, amount, status, due_date, event_timestamp])

    def insert_stock_event(self, event_type: str, sku: str, order_id: str,
                          qty_reserved: int, event_timestamp: datetime):
        """Insert raw stock event"""
        self.conn.execute("""
            INSERT INTO stock_events (event_type, sku, order_id, qty_reserved, event_timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, [event_type, sku, order_id, qty_reserved, event_timestamp])

    def get_sales_summary(self, hours: int = 24):
        """Get sales summary for last N hours"""
        return self.conn.execute(f"""
            SELECT * FROM sales_by_hour
            WHERE hour >= CURRENT_TIMESTAMP - INTERVAL '{hours} hours'
            ORDER BY hour DESC
        """).fetchall()

    def get_low_stock_items(self):
        """Get items that need reordering"""
        return self.conn.execute("""
            SELECT * FROM stock_snapshot
            WHERE needs_reorder = TRUE
            ORDER BY available_qty ASC
        """).fetchall()


# Global client instance
duckdb_client = DuckDBClient()
