"""OLAP Query API Router"""
import time
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.duckdb_client import duckdb_client
from app.schemas import (
    QueryRequest,
    QueryResponse,
    PredefinedQuery,
    SalesByHourResponse,
    SalesByHourRow,
    LowStockResponse,
    LowStockRow,
    OverdueARResponse,
    OverdueARRow,
    DailyOrderResponse,
    DailyOrderRow,
    StockMovementResponse,
    StockMovementRow,
)


router = APIRouter(prefix="/query", tags=["OLAP Queries"])


# Predefined safe queries (prevents SQL injection)
PREDEFINED_QUERIES: Dict[str, str] = {
    "sales_24h": """
        SELECT hour, total_orders, total_revenue, avg_order_value, unique_customers, updated_at
        FROM sales_by_hour
        WHERE hour >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ORDER BY hour DESC
        LIMIT ?
    """,
    "sales_7d": """
        SELECT hour, total_orders, total_revenue, avg_order_value, unique_customers, updated_at
        FROM sales_by_hour
        WHERE hour >= CURRENT_TIMESTAMP - INTERVAL '7 days'
        ORDER BY hour DESC
        LIMIT ?
    """,
    "low_stock": """
        SELECT sku, product_name, qty_on_hand, reserved_qty, available_qty, reorder_point, last_updated
        FROM stock_snapshot
        WHERE needs_reorder = TRUE
        ORDER BY available_qty ASC
        LIMIT ?
    """,
    "overdue_ar": """
        SELECT customer_id, customer_name, total_outstanding, days_30, days_60, days_90_plus,
               oldest_invoice_date, DATEDIFF('day', oldest_invoice_date, CURRENT_DATE) AS days_overdue
        FROM ar_aging
        WHERE total_outstanding > 0
        ORDER BY days_overdue DESC
        LIMIT ?
    """,
    "daily_orders": """
        SELECT order_date, total_orders, total_revenue, avg_order_value
        FROM daily_order_volume
        WHERE order_date >= CURRENT_DATE - INTERVAL '? days'
        ORDER BY order_date DESC
        LIMIT ?
    """,
    "stock_movement": """
        SELECT sku, total_reservations, total_qty_reserved, first_reservation, last_reservation
        FROM stock_movement_summary
        ORDER BY total_qty_reserved DESC
        LIMIT ?
    """,
    "top_customers": """
        SELECT customer_id, customer_name, total_outstanding
        FROM ar_aging
        ORDER BY total_outstanding DESC
        LIMIT ?
    """,
    "revenue_by_day": """
        SELECT DATE_TRUNC('day', event_timestamp) AS order_date,
               COUNT(DISTINCT order_id) AS total_orders,
               SUM(total_amount) AS total_revenue,
               AVG(total_amount) AS avg_order_value
        FROM order_events
        WHERE event_type = 'order_created'
          AND event_timestamp >= CURRENT_DATE - INTERVAL '? days'
        GROUP BY DATE_TRUNC('day', event_timestamp)
        ORDER BY order_date DESC
        LIMIT ?
    """,
}


@router.post("/execute", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a predefined OLAP query

    Only predefined queries are allowed to prevent SQL injection.
    """
    try:
        query_name = request.query_name.value

        if query_name not in PREDEFINED_QUERIES:
            raise HTTPException(status_code=400, detail=f"Unknown query: {query_name}")

        sql = PREDEFINED_QUERIES[query_name]
        limit = request.limit or 100

        # Start timing
        start_time = time.time()

        # Execute query with parameterized limit
        result = duckdb_client.conn.execute(sql, [limit])

        # Fetch results
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        return QueryResponse(
            query_name=query_name,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=round(execution_time_ms, 2),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.get("/sales/hourly", response_model=SalesByHourResponse)
async def get_sales_hourly(hours: int = Query(24, ge=1, le=168, description="Number of hours (max 7 days)")):
    """Get hourly sales summary"""
    try:
        results = duckdb_client.conn.execute("""
            SELECT hour, total_orders, total_revenue, avg_order_value, unique_customers, updated_at
            FROM sales_by_hour
            WHERE hour >= CURRENT_TIMESTAMP - INTERVAL ? ' hours'
            ORDER BY hour DESC
        """, [hours]).fetchall()

        return SalesByHourResponse(
            hours=hours,
            data=[
                SalesByHourRow(
                    hour=str(row[0]),
                    total_orders=row[1],
                    total_revenue=float(row[2]),
                    avg_order_value=float(row[3]),
                    unique_customers=row[4],
                    updated_at=str(row[5]),
                )
                for row in results
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/low-stock", response_model=LowStockResponse)
async def get_low_stock_items():
    """Get items that need reordering"""
    try:
        results = duckdb_client.conn.execute("""
            SELECT sku, product_name, qty_on_hand, reserved_qty, available_qty, reorder_point, last_updated
            FROM stock_snapshot
            WHERE needs_reorder = TRUE
            ORDER BY available_qty ASC
        """).fetchall()

        return LowStockResponse(
            items=[
                LowStockRow(
                    sku=row[0],
                    product_name=row[1],
                    qty_on_hand=row[2],
                    reserved_qty=row[3],
                    available_qty=row[4],
                    reorder_point=row[5],
                    last_updated=str(row[6]),
                )
                for row in results
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ar/overdue", response_model=OverdueARResponse)
async def get_overdue_ar():
    """Get customers with overdue invoices"""
    try:
        results = duckdb_client.conn.execute("""
            SELECT customer_id, customer_name, total_outstanding, days_30, days_60, days_90_plus,
                   oldest_invoice_date, DATEDIFF('day', oldest_invoice_date, CURRENT_DATE) AS days_overdue
            FROM ar_aging
            WHERE total_outstanding > 0
            ORDER BY days_overdue DESC
        """).fetchall()

        return OverdueARResponse(
            items=[
                OverdueARRow(
                    customer_id=str(row[0]),
                    customer_name=row[1],
                    total_outstanding=float(row[2]),
                    days_30=float(row[3]),
                    days_60=float(row[4]),
                    days_90_plus=float(row[5]),
                    oldest_invoice_date=str(row[6]),
                    days_overdue=row[7],
                )
                for row in results
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/daily", response_model=DailyOrderResponse)
async def get_daily_orders(days: int = Query(30, ge=1, le=365, description="Number of days")):
    """Get daily order volume and revenue"""
    try:
        results = duckdb_client.conn.execute("""
            SELECT order_date, total_orders, total_revenue, avg_order_value
            FROM daily_order_volume
            WHERE order_date >= CURRENT_DATE - INTERVAL ? ' days'
            ORDER BY order_date DESC
        """, [days]).fetchall()

        return DailyOrderResponse(
            days=days,
            data=[
                DailyOrderRow(
                    order_date=str(row[0]),
                    total_orders=row[1],
                    total_revenue=float(row[2]),
                    avg_order_value=float(row[3]),
                )
                for row in results
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/movement", response_model=StockMovementResponse)
async def get_stock_movement(limit: int = Query(50, ge=1, le=500)):
    """Get stock movement summary"""
    try:
        results = duckdb_client.conn.execute("""
            SELECT sku, total_reservations, total_qty_reserved, first_reservation, last_reservation
            FROM stock_movement_summary
            ORDER BY total_qty_reserved DESC
            LIMIT ?
        """, [limit]).fetchall()

        return StockMovementResponse(
            items=[
                StockMovementRow(
                    sku=row[0],
                    total_reservations=row[1],
                    total_qty_reserved=row[2],
                    first_reservation=str(row[3]),
                    last_reservation=str(row[4]),
                )
                for row in results
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def list_available_queries():
    """List all available predefined queries"""
    return JSONResponse(
        content={
            "queries": [
                {
                    "name": query_name,
                    "description": get_query_description(query_name),
                    "endpoint": get_query_endpoint(query_name),
                }
                for query_name in PREDEFINED_QUERIES.keys()
            ]
        }
    )


def get_query_description(query_name: str) -> str:
    """Get description for a query"""
    descriptions = {
        "sales_24h": "Hourly sales for last 24 hours",
        "sales_7d": "Hourly sales for last 7 days",
        "low_stock": "Items that need reordering",
        "overdue_ar": "Customers with overdue invoices",
        "daily_orders": "Daily order volume and revenue",
        "stock_movement": "Stock reservation summary by SKU",
        "top_customers": "Top customers by outstanding AR",
        "revenue_by_day": "Revenue aggregated by day",
    }
    return descriptions.get(query_name, "")


def get_query_endpoint(query_name: str) -> str:
    """Get REST endpoint for a query"""
    endpoints = {
        "sales_24h": "GET /query/sales/hourly?hours=24",
        "sales_7d": "GET /query/sales/hourly?hours=168",
        "low_stock": "GET /query/inventory/low-stock",
        "overdue_ar": "GET /query/ar/overdue",
        "daily_orders": "GET /query/orders/daily?days=30",
        "stock_movement": "GET /query/inventory/movement",
        "top_customers": "POST /query/execute (query_name=top_customers)",
        "revenue_by_day": "POST /query/execute (query_name=revenue_by_day)",
    }
    return endpoints.get(query_name, "POST /query/execute")
