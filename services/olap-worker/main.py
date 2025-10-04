"""OLAP Worker - NATS Event Consumer for DuckDB"""
import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.nats_client import nats_client
from app.duckdb_client import duckdb_client
from app.consumers.event_consumer import olap_consumer
from app.routers import query


# Global flag for graceful shutdown
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("Starting OLAP Worker...")
    duckdb_client.connect()
    await nats_client.connect()

    # Start consumer in background
    consumer_task = asyncio.create_task(olap_consumer.start())

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print(f"\nReceived signal {sig}, shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    yield

    # Shutdown
    print("Shutting down OLAP Worker...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await nats_client.close()
    duckdb_client.close()


app = FastAPI(
    title="OLAP Query API",
    description="NATS Event Consumer & DuckDB Query API for Real-time Analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include query router
app.include_router(query.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "olap-worker",
            "nats_connected": nats_client.nc is not None and nats_client.nc.is_connected,
            "duckdb_connected": duckdb_client.conn is not None,
        }
    )


@app.get("/stats")
async def get_stats():
    """Get processing statistics"""
    return JSONResponse(
        content={
            "events_processed": len(olap_consumer.processed_events),
            "consumer_name": olap_consumer.consumer_name,
        }
    )


@app.get("/sales/summary")
async def get_sales_summary(hours: int = 24):
    """Get sales summary for last N hours"""
    try:
        results = duckdb_client.get_sales_summary(hours)
        return JSONResponse(
            content={
                "hours": hours,
                "data": [
                    {
                        "hour": str(row[0]),
                        "total_orders": row[1],
                        "total_revenue": float(row[2]),
                        "avg_order_value": float(row[3]),
                        "updated_at": str(row[4]),
                    }
                    for row in results
                ],
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@app.get("/inventory/low-stock")
async def get_low_stock():
    """Get items that need reordering"""
    try:
        results = duckdb_client.get_low_stock_items()
        return JSONResponse(
            content={
                "items": [
                    {
                        "sku": row[0],
                        "product_name": row[1],
                        "qty_on_hand": row[2],
                        "reserved_qty": row[3],
                        "available_qty": row[4],
                        "reorder_point": row[5],
                        "last_updated": str(row[7]),
                    }
                    for row in results
                ],
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
