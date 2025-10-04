"""
Orders Service - FastAPI Application
Handles order creation, retrieval, and status updates
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, init_db
from app.nats_client import nats_client
from app.routers import orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    await init_db()
    await nats_client.connect()
    yield
    # Shutdown
    await nats_client.close()
    await engine.dispose()


app = FastAPI(
    title="Orders Service",
    description="Order management microservice for Pulse ERP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders.router, prefix="/orders", tags=["orders"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "orders"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    return {"message": "Metrics endpoint - to be implemented with prometheus_client"}
