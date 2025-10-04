"""
Billing Service - FastAPI Application
Handles invoicing, payments, and accounting ledger
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, init_db
from app.nats_client import nats_client
from app.routers import billing
from app.consumers.order_consumer import order_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    await init_db()
    await nats_client.connect()

    # Start NATS consumer in background
    consumer_task = asyncio.create_task(order_consumer.start())

    yield

    # Shutdown
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await nats_client.close()
    await engine.dispose()


app = FastAPI(
    title="Billing Service",
    description="Invoice and payment management for Pulse ERP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(billing.router, prefix="/billing", tags=["billing"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "billing"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    return {"message": "Metrics endpoint - to be implemented"}
