// Order types
export interface Order {
  id: string;
  customer_id: string;
  status: 'draft' | 'placed' | 'cancelled' | 'shipped' | 'completed';
  total_amount: number;
  created_at: string;
  updated_at: string;
  items?: OrderItem[];
}

export interface OrderItem {
  id: string;
  order_id: string;
  sku: string;
  qty: number;
  price: number;
}

export interface CreateOrderRequest {
  customer_id: string;
  items: {
    sku: string;
    qty: number;
    price: number;
  }[];
}

// Inventory types
export interface Product {
  sku: string;
  name: string;
  description?: string;
  price: number;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
  inventory?: InventoryItem;
}

export interface InventoryItem {
  sku: string;
  qty_on_hand: number | null;
  reserved_qty: number | null;
}

export interface StockReservationRequest {
  order_id: string;
  qty: number;
}

// Billing types
export interface Invoice {
  id: string;
  order_id: string;
  amount: number;
  status: 'issued' | 'paid' | 'cancelled';
  issued_at: string;
  due_date: string;
  paid_at?: string;
}

// Analytics types
export interface SalesHourly {
  hour: string;
  total_orders: number;
  total_revenue: number;
  avg_order_value: number;
  unique_customers: number;
  updated_at: string;
}

export interface LowStockItem {
  sku: string;
  product_name: string;
  qty_on_hand: number;
  reserved_qty: number;
  available_qty: number;
  reorder_point: number;
  last_updated: string;
}

export interface OverdueAR {
  customer_id: string;
  customer_name: string;
  total_outstanding: number;
  days_30: number;
  days_60: number;
  days_90_plus: number;
  oldest_invoice_date: string;
  days_overdue: number;
}

export interface DailyOrder {
  order_date: string;
  total_orders: number;
  total_revenue: number;
  avg_order_value: number;
}
