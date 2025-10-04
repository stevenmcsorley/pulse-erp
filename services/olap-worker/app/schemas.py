"""Pydantic Schemas for OLAP Query API"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class PredefinedQuery(str, Enum):
    """Predefined safe queries"""
    SALES_24H = "sales_24h"
    SALES_7D = "sales_7d"
    LOW_STOCK = "low_stock"
    OVERDUE_AR = "overdue_ar"
    DAILY_ORDERS = "daily_orders"
    STOCK_MOVEMENT = "stock_movement"
    TOP_CUSTOMERS = "top_customers"
    REVENUE_BY_DAY = "revenue_by_day"


class QueryRequest(BaseModel):
    """Request for custom SQL query"""
    query_name: PredefinedQuery = Field(..., description="Predefined query name")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Result limit")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query parameters")


class QueryResponse(BaseModel):
    """Response from query execution"""
    query_name: str = Field(..., description="Query that was executed")
    columns: List[str] = Field(..., description="Column names")
    rows: List[List[Any]] = Field(..., description="Result rows")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")


class SalesByHourRow(BaseModel):
    """Sales by hour data"""
    hour: str
    total_orders: int
    total_revenue: float
    avg_order_value: float
    unique_customers: int
    updated_at: str


class SalesByHourResponse(BaseModel):
    """Sales summary response"""
    hours: int
    data: List[SalesByHourRow]


class LowStockRow(BaseModel):
    """Low stock item"""
    sku: str
    product_name: str
    qty_on_hand: int
    reserved_qty: int
    available_qty: int
    reorder_point: int
    last_updated: str


class LowStockResponse(BaseModel):
    """Low stock items response"""
    items: List[LowStockRow]


class OverdueARRow(BaseModel):
    """Overdue AR record"""
    customer_id: str
    customer_name: str
    total_outstanding: float
    days_30: float
    days_60: float
    days_90_plus: float
    oldest_invoice_date: str
    days_overdue: int


class OverdueARResponse(BaseModel):
    """Overdue AR response"""
    items: List[OverdueARRow]


class DailyOrderRow(BaseModel):
    """Daily order volume"""
    order_date: str
    total_orders: int
    total_revenue: float
    avg_order_value: float


class DailyOrderResponse(BaseModel):
    """Daily order volume response"""
    days: int
    data: List[DailyOrderRow]


class StockMovementRow(BaseModel):
    """Stock movement summary"""
    sku: str
    total_reservations: int
    total_qty_reserved: int
    first_reservation: str
    last_reservation: str


class StockMovementResponse(BaseModel):
    """Stock movement response"""
    items: List[StockMovementRow]
