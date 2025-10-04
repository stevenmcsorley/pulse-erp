-- =====================================================
-- DuckDB OLAP Schema - Rollback Script
-- Version: 001
-- Purpose: Rollback initial OLAP schema
-- =====================================================

-- Drop views first (dependent objects)
DROP VIEW IF EXISTS stock_movement_summary;
DROP VIEW IF EXISTS daily_order_volume;
DROP VIEW IF EXISTS overdue_ar;
DROP VIEW IF EXISTS low_stock_items;
DROP VIEW IF EXISTS sales_summary_24h;

-- Drop indexes
DROP INDEX IF EXISTS idx_stock_events_timestamp;
DROP INDEX IF EXISTS idx_stock_events_order_id;
DROP INDEX IF EXISTS idx_stock_events_sku;

DROP INDEX IF EXISTS idx_invoice_events_timestamp;
DROP INDEX IF EXISTS idx_invoice_events_order_id;
DROP INDEX IF EXISTS idx_invoice_events_invoice_id;

DROP INDEX IF EXISTS idx_order_events_customer_id;
DROP INDEX IF EXISTS idx_order_events_timestamp;
DROP INDEX IF EXISTS idx_order_events_order_id;

-- Drop raw event tables
DROP TABLE IF EXISTS stock_events;
DROP TABLE IF EXISTS invoice_events;
DROP TABLE IF EXISTS order_events;

-- Drop aggregate tables
DROP TABLE IF EXISTS ar_aging;
DROP TABLE IF EXISTS stock_snapshot;
DROP TABLE IF EXISTS sales_by_hour;

-- Drop sequences
DROP SEQUENCE IF EXISTS stock_events_seq;
DROP SEQUENCE IF EXISTS invoice_events_seq;
DROP SEQUENCE IF EXISTS order_events_seq;

-- Drop metadata
DROP TABLE IF EXISTS schema_version;
