-- Pulse ERP - Rollback Initial Schema
-- Migration: 001_initial_schema_rollback
-- Description: Drops all tables and views created in 001_initial_schema.sql

-- Drop views first (depend on tables)
DROP VIEW IF EXISTS account_balances CASCADE;
DROP VIEW IF EXISTS invoice_details CASCADE;
DROP VIEW IF EXISTS inventory_status CASCADE;
DROP VIEW IF EXISTS order_details CASCADE;

-- Drop triggers
DROP TRIGGER IF EXISTS update_employees_updated_at ON employees;
DROP TRIGGER IF EXISTS update_invoices_updated_at ON invoices;
DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
DROP TRIGGER IF EXISTS update_inventory_items_updated_at ON inventory_items;
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS events_log CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS ledger_entries CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS inventory_items CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Note: UUID extension is not dropped as it may be used by other applications
-- DROP EXTENSION IF EXISTS "uuid-ossp";
