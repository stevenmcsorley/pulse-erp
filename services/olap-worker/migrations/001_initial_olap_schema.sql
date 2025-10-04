-- =====================================================
-- DuckDB OLAP Schema - Initial Setup
-- Version: 001
-- Created: 2025-10-04
-- Purpose: Analytical tables for Pulse ERP
-- =====================================================

-- Enable sequences for auto-incrementing IDs
CREATE SEQUENCE IF NOT EXISTS order_events_seq START 1;
CREATE SEQUENCE IF NOT EXISTS invoice_events_seq START 1;
CREATE SEQUENCE IF NOT EXISTS stock_events_seq START 1;

-- =====================================================
-- AGGREGATE TABLES (Pre-computed for dashboards)
-- =====================================================

-- Sales by Hour - Aggregated sales metrics
CREATE TABLE IF NOT EXISTS sales_by_hour (
    hour TIMESTAMP PRIMARY KEY,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(14,2) DEFAULT 0,
    avg_order_value DECIMAL(14,2) DEFAULT 0,
    unique_customers INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Snapshot - Point-in-time inventory levels
CREATE TABLE IF NOT EXISTS stock_snapshot (
    sku VARCHAR PRIMARY KEY,
    product_name VARCHAR,
    qty_on_hand INTEGER DEFAULT 0,
    reserved_qty INTEGER DEFAULT 0,
    available_qty INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 10,
    needs_reorder BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AR Aging - Accounts Receivable aging buckets
CREATE TABLE IF NOT EXISTS ar_aging (
    customer_id UUID PRIMARY KEY,
    customer_name VARCHAR,
    total_outstanding DECIMAL(14,2) DEFAULT 0,
    current_amount DECIMAL(14,2) DEFAULT 0,
    days_30 DECIMAL(14,2) DEFAULT 0,
    days_60 DECIMAL(14,2) DEFAULT 0,
    days_90_plus DECIMAL(14,2) DEFAULT 0,
    oldest_invoice_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- RAW EVENT TABLES (Event sourcing for analytics)
-- =====================================================

-- Order Events - All order-related events
CREATE TABLE IF NOT EXISTS order_events (
    id INTEGER PRIMARY KEY DEFAULT nextval('order_events_seq'),
    order_id UUID NOT NULL,
    event_type VARCHAR NOT NULL,
    customer_id UUID,
    total_amount DECIMAL(14,2),
    status VARCHAR,
    event_timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice Events - All invoice-related events
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
);

-- Stock Events - All inventory-related events
CREATE TABLE IF NOT EXISTS stock_events (
    id INTEGER PRIMARY KEY DEFAULT nextval('stock_events_seq'),
    event_type VARCHAR NOT NULL,
    sku VARCHAR NOT NULL,
    order_id UUID,
    qty_reserved INTEGER,
    event_timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES for Query Performance
-- =====================================================

-- Order events indexes
CREATE INDEX IF NOT EXISTS idx_order_events_order_id ON order_events(order_id);
CREATE INDEX IF NOT EXISTS idx_order_events_timestamp ON order_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_order_events_customer_id ON order_events(customer_id);

-- Invoice events indexes
CREATE INDEX IF NOT EXISTS idx_invoice_events_invoice_id ON invoice_events(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_events_order_id ON invoice_events(order_id);
CREATE INDEX IF NOT EXISTS idx_invoice_events_timestamp ON invoice_events(event_timestamp);

-- Stock events indexes
CREATE INDEX IF NOT EXISTS idx_stock_events_sku ON stock_events(sku);
CREATE INDEX IF NOT EXISTS idx_stock_events_order_id ON stock_events(order_id);
CREATE INDEX IF NOT EXISTS idx_stock_events_timestamp ON stock_events(event_timestamp);

-- =====================================================
-- ANALYTICAL VIEWS
-- =====================================================

-- Sales Summary View - Last 24 hours
CREATE OR REPLACE VIEW sales_summary_24h AS
SELECT
    hour,
    total_orders,
    total_revenue,
    avg_order_value,
    unique_customers
FROM sales_by_hour
WHERE hour >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY hour DESC;

-- Low Stock Alert View
CREATE OR REPLACE VIEW low_stock_items AS
SELECT
    sku,
    product_name,
    qty_on_hand,
    reserved_qty,
    available_qty,
    reorder_point,
    last_updated
FROM stock_snapshot
WHERE needs_reorder = TRUE
ORDER BY available_qty ASC;

-- Overdue Invoices View
CREATE OR REPLACE VIEW overdue_ar AS
SELECT
    customer_id,
    customer_name,
    total_outstanding,
    days_30,
    days_60,
    days_90_plus,
    oldest_invoice_date,
    DATEDIFF('day', oldest_invoice_date, CURRENT_DATE) AS days_overdue
FROM ar_aging
WHERE total_outstanding > 0
ORDER BY days_overdue DESC;

-- Order Volume Trend - Daily summary
CREATE OR REPLACE VIEW daily_order_volume AS
SELECT
    DATE_TRUNC('day', event_timestamp) AS order_date,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value
FROM order_events
WHERE event_type = 'order_created'
GROUP BY DATE_TRUNC('day', event_timestamp)
ORDER BY order_date DESC;

-- Stock Movement Analysis
CREATE OR REPLACE VIEW stock_movement_summary AS
SELECT
    sku,
    COUNT(*) AS total_reservations,
    SUM(qty_reserved) AS total_qty_reserved,
    MIN(event_timestamp) AS first_reservation,
    MAX(event_timestamp) AS last_reservation
FROM stock_events
WHERE event_type = 'stock_reserved'
GROUP BY sku
ORDER BY total_qty_reserved DESC;

-- =====================================================
-- SEED DATA for Testing
-- =====================================================

-- Sample sales data
INSERT INTO sales_by_hour (hour, total_orders, total_revenue, avg_order_value, unique_customers)
VALUES
    (DATE_TRUNC('hour', CURRENT_TIMESTAMP - INTERVAL '1 hour'), 5, 450.00, 90.00, 5),
    (DATE_TRUNC('hour', CURRENT_TIMESTAMP - INTERVAL '2 hours'), 8, 720.00, 90.00, 7),
    (DATE_TRUNC('hour', CURRENT_TIMESTAMP - INTERVAL '3 hours'), 3, 280.00, 93.33, 3)
ON CONFLICT (hour) DO NOTHING;

-- Sample stock snapshot
INSERT INTO stock_snapshot (sku, product_name, qty_on_hand, reserved_qty, available_qty, reorder_point, needs_reorder)
VALUES
    ('WIDGET-001', 'Blue Widget', 100, 10, 90, 20, FALSE),
    ('WIDGET-002', 'Red Widget', 15, 5, 10, 20, TRUE),
    ('GADGET-001', 'Super Gadget', 50, 20, 30, 25, FALSE)
ON CONFLICT (sku) DO NOTHING;

-- Sample AR aging
INSERT INTO ar_aging (customer_id, customer_name, total_outstanding, current_amount, days_30, days_60, days_90_plus, oldest_invoice_date)
VALUES
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'Acme Corp', 5000.00, 2000.00, 2000.00, 1000.00, 0.00, CURRENT_DATE - INTERVAL '35 days'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'TechStart Inc', 1500.00, 1500.00, 0.00, 0.00, 0.00, CURRENT_DATE - INTERVAL '10 days')
ON CONFLICT (customer_id) DO NOTHING;

-- =====================================================
-- Schema Metadata
-- =====================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR
);

INSERT INTO schema_version (version, description)
VALUES (1, 'Initial OLAP schema with aggregate and event tables')
ON CONFLICT (version) DO NOTHING;
