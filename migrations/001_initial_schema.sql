-- Pulse ERP - Initial Database Schema
-- Migration: 001_initial_schema
-- Created: 2025-10-04
-- Description: Creates all core tables for Orders, Inventory, Billing, HR, and Events

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CUSTOMERS
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_created_at ON customers(created_at DESC);

-- ============================================
-- PRODUCTS
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    sku VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_products_name ON products(name text_pattern_ops);

-- ============================================
-- INVENTORY ITEMS
-- ============================================
CREATE TABLE IF NOT EXISTS inventory_items (
    sku VARCHAR(64) PRIMARY KEY REFERENCES products(sku) ON DELETE CASCADE,
    qty_on_hand INTEGER NOT NULL DEFAULT 0 CHECK (qty_on_hand >= 0),
    reserved_qty INTEGER NOT NULL DEFAULT 0 CHECK (reserved_qty >= 0),
    reorder_point INTEGER NOT NULL DEFAULT 0 CHECK (reorder_point >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT qty_check CHECK (reserved_qty <= qty_on_hand)
);

-- ============================================
-- ORDERS
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    status VARCHAR(32) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'placed', 'cancelled', 'shipped', 'completed')),
    total_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_orders_customer ON orders(customer_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- ============================================
-- ORDER ITEMS
-- ============================================
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sku VARCHAR(64) NOT NULL REFERENCES products(sku) ON DELETE RESTRICT,
    qty INTEGER NOT NULL CHECK (qty > 0),
    price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_sku ON order_items(sku);

-- ============================================
-- INVOICES
-- ============================================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
    status VARCHAR(32) NOT NULL DEFAULT 'issued'
        CHECK (status IN ('issued', 'paid', 'overdue', 'cancelled')),
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date DATE NOT NULL,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_invoices_order ON invoices(order_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_invoices_issued_at ON invoices(issued_at DESC);

-- ============================================
-- LEDGER ENTRIES (Double-Entry Accounting)
-- ============================================
CREATE TABLE IF NOT EXISTS ledger_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account VARCHAR(64) NOT NULL,
    debit NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (debit >= 0),
    credit NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (credit >= 0),
    ref_type VARCHAR(32) NOT NULL CHECK (ref_type IN ('order', 'invoice', 'payment', 'payroll', 'adjustment')),
    ref_id UUID NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ledger_entry_check CHECK (
        (debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)
    )
);

CREATE INDEX idx_ledger_account ON ledger_entries(account, created_at DESC);
CREATE INDEX idx_ledger_ref ON ledger_entries(ref_type, ref_id);
CREATE INDEX idx_ledger_created_at ON ledger_entries(created_at DESC);

-- ============================================
-- EMPLOYEES (Minimal MVP)
-- ============================================
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(64) NOT NULL,
    salary_pence INTEGER NOT NULL DEFAULT 0 CHECK (salary_pence >= 0),
    payroll_meta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_active ON employees(active);

-- ============================================
-- EVENTS LOG (Audit Trail - Append Only)
-- ============================================
CREATE TABLE IF NOT EXISTS events_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    source VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_type ON events_log(event_type);
CREATE INDEX idx_events_source ON events_log(source);
CREATE INDEX idx_events_recorded_at ON events_log(recorded_at DESC);

-- ============================================
-- UPDATED_AT TRIGGER FUNCTION
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inventory_items_updated_at BEFORE UPDATE ON inventory_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employees_updated_at BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Order details with items
CREATE OR REPLACE VIEW order_details AS
SELECT
    o.id,
    o.customer_id,
    c.name as customer_name,
    c.email as customer_email,
    o.status,
    o.total_amount,
    o.created_at,
    o.updated_at,
    json_agg(
        json_build_object(
            'sku', oi.sku,
            'product_name', p.name,
            'qty', oi.qty,
            'price', oi.price,
            'line_total', oi.qty * oi.price
        ) ORDER BY oi.created_at
    ) as items
FROM orders o
JOIN customers c ON o.customer_id = c.id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.sku = p.sku
GROUP BY o.id, c.id;

-- Inventory with product details
CREATE OR REPLACE VIEW inventory_status AS
SELECT
    p.sku,
    p.name,
    p.description,
    p.price,
    COALESCE(i.qty_on_hand, 0) as qty_on_hand,
    COALESCE(i.reserved_qty, 0) as reserved_qty,
    COALESCE(i.qty_on_hand, 0) - COALESCE(i.reserved_qty, 0) as available_qty,
    COALESCE(i.reorder_point, 0) as reorder_point,
    CASE
        WHEN COALESCE(i.qty_on_hand, 0) - COALESCE(i.reserved_qty, 0) <= COALESCE(i.reorder_point, 0)
        THEN TRUE
        ELSE FALSE
    END as needs_reorder,
    i.updated_at
FROM products p
LEFT JOIN inventory_items i ON p.sku = i.sku;

-- Invoice details
CREATE OR REPLACE VIEW invoice_details AS
SELECT
    i.id,
    i.order_id,
    o.customer_id,
    c.name as customer_name,
    c.email as customer_email,
    i.amount,
    i.status,
    i.issued_at,
    i.due_date,
    i.paid_at,
    CASE
        WHEN i.status = 'paid' THEN 0
        WHEN i.due_date < CURRENT_DATE AND i.status != 'paid' THEN
            EXTRACT(DAY FROM CURRENT_DATE - i.due_date)
        ELSE 0
    END as days_overdue
FROM invoices i
JOIN orders o ON i.order_id = o.id
JOIN customers c ON o.customer_id = c.id;

-- Account balances (simple ledger view)
CREATE OR REPLACE VIEW account_balances AS
SELECT
    account,
    SUM(debit) as total_debit,
    SUM(credit) as total_credit,
    SUM(debit - credit) as balance,
    COUNT(*) as entry_count,
    MAX(created_at) as last_transaction
FROM ledger_entries
GROUP BY account;

-- ============================================
-- GRANT PERMISSIONS (for application user)
-- ============================================
-- Note: Adjust username based on POSTGRES_USER environment variable
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pulseadmin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pulseadmin;

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================
COMMENT ON TABLE customers IS 'Customer master data';
COMMENT ON TABLE products IS 'Product catalog with pricing';
COMMENT ON TABLE inventory_items IS 'Stock levels and reservations per SKU';
COMMENT ON TABLE orders IS 'Customer orders with status tracking';
COMMENT ON TABLE order_items IS 'Line items for each order';
COMMENT ON TABLE invoices IS 'Invoices generated from orders';
COMMENT ON TABLE ledger_entries IS 'Double-entry accounting ledger (append-only)';
COMMENT ON TABLE employees IS 'Employee records for HR/Payroll';
COMMENT ON TABLE events_log IS 'Domain events audit log (append-only)';

COMMENT ON VIEW order_details IS 'Orders with customer and item details';
COMMENT ON VIEW inventory_status IS 'Current inventory status with reorder flags';
COMMENT ON VIEW invoice_details IS 'Invoices with customer and aging info';
COMMENT ON VIEW account_balances IS 'Account balances from ledger entries';
