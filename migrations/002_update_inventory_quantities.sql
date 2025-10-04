-- 002_update_inventory_quantities.sql
-- Update existing NULL values for qty_on_hand and reserved_qty to 0

UPDATE inventory_items
SET
    qty_on_hand = COALESCE(qty_on_hand, 0),
    reserved_qty = COALESCE(reserved_qty, 0)
WHERE
    qty_on_hand IS NULL OR reserved_qty IS NULL;