"""
SecurePay Webhook Service — FastAPI Application
================================================
A production-grade payment transaction webhook receiver
with idempotency, structured logging, and Prometheus metrics.

Designed for deployment on hardened AWS EKS via ArgoCD GitOps.
"""

import json
import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import find_transaction, get_session, init_db, store_transaction
from models import (
    DuplicateResponse,
    ErrorResponse,
    HealthResponse,
    TransactionResponse,
    TransactionWebhook,
)


# --- Structured JSON Logging ---

class JSONFormatter(logging.Formatter):
    """Structured JSON log format for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """Configure structured JSON logging."""
    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger("webhook-service")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()

# --- Prometheus Metrics ---

WEBHOOK_REQUESTS_TOTAL = Counter(
    "webhook_requests_total",
    "Total webhook requests received",
    ["method", "endpoint", "status_code"],
)

WEBHOOK_PROCESSING_SECONDS = Histogram(
    "webhook_processing_duration_seconds",
    "Time spent processing webhook requests",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

TRANSACTION_STATUS_TOTAL = Counter(
    "transaction_status_total",
    "Transactions received by status",
    ["status", "payment_method"],
)


# --- Application Lifespan ---

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup, cleanup on shutdown."""
    logger.info("Starting webhook service — initializing database")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    logger.info("Shutting down webhook service")


# --- FastAPI App ---

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production payment transaction webhook receiver "
        "with idempotency, structured logging, and Prometheus metrics. "
        "Part of the Fintech DevSecOps Pipeline."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- Middleware: Request Logging & Metrics ---

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request duration and count per endpoint."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    endpoint = request.url.path
    WEBHOOK_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code,
    ).inc()
    WEBHOOK_PROCESSING_SECONDS.labels(endpoint=endpoint).observe(duration)

    logger.info(
        f"{request.method} {endpoint} → {response.status_code} ({duration:.4f}s)"
    )
    return response


# --- Endpoints ---

@app.post(
    "/webhook/transaction",
    response_model=TransactionResponse,
    status_code=200,
    responses={
        409: {"model": DuplicateResponse, "description": "Duplicate transaction"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    summary="Receive payment transaction webhook",
    description=(
        "Receives a transaction webhook from the payment gateway. "
        "Implements idempotency via transaction_id deduplication."
    ),
)
async def receive_transaction(
    payload: TransactionWebhook,
    session: AsyncSession = Depends(get_session),
):
    """
    Process incoming payment webhook:
    1. Check for duplicate transaction_id (idempotency)
    2. Validate and store the transaction
    3. Return confirmation with internal ID
    """
    logger.info(
        f"Received webhook: txn={payload.transaction_id} "
        f"merchant={payload.merchant_id} amount={payload.amount} "
        f"status={payload.status.value} method={payload.payment_method.value}"
    )

    # Idempotency check — reject duplicate transaction IDs
    existing = await find_transaction(session, payload.transaction_id)
    if existing:
        logger.warning(
            f"Duplicate transaction_id: {payload.transaction_id} "
            f"(originally received at {existing.received_at})"
        )
        raise HTTPException(
            status_code=409,
            detail={
                "detail": "Transaction already processed",
                "transaction_id": payload.transaction_id,
                "original_received_at": existing.received_at.isoformat(),
            },
        )

    # Store the transaction
    metadata_str = json.dumps(payload.metadata) if payload.metadata else None
    record = await store_transaction(
        session=session,
        transaction_id=payload.transaction_id,
        merchant_id=payload.merchant_id,
        amount=payload.amount,
        currency=payload.currency,
        status=payload.status.value,
        payment_method=payload.payment_method.value,
        customer_email=payload.customer_email,
        metadata_json=metadata_str,
    )

    # Track metrics by status + payment method
    TRANSACTION_STATUS_TOTAL.labels(
        status=payload.status.value,
        payment_method=payload.payment_method.value,
    ).inc()

    logger.info(
        f"Transaction stored: id={record.id} txn={record.transaction_id}"
    )

    return TransactionResponse(
        id=record.id,
        transaction_id=record.transaction_id,
        merchant_id=record.merchant_id,
        amount=record.amount,
        currency=record.currency,
        status=payload.status,
        payment_method=payload.payment_method,
        received_at=record.received_at,
        message="Webhook processed successfully",
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Kubernetes liveness/readiness probe endpoint.",
)
async def health_check():
    """Health check for K8s probes — returns uptime and DB status."""
    uptime = time.time() - START_TIME

    # Simple DB connectivity check
    db_status = "connected"
    try:
        async for session in get_session():
            await session.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="webhook-service",
        version=settings.APP_VERSION,
        database=db_status,
        uptime_seconds=round(uptime, 2),
    )


@app.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Prometheus-compatible metrics endpoint for observability.",
)
async def metrics():
    """Expose Prometheus metrics for scraping."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
        <head><title>SecurePay Webhook Monitor</title></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: 40px auto;">
            <h1>🛡️ Payment Webhook Service</h1>
            <p><strong>Status:</strong> ✅ Operational</p>
            <p><strong>Endpoints:</strong></p>
            <ul>
                <li><code>POST /webhook/transaction</code> — Receive payment events</li>
                <li><code>GET /health</code> — Health check</li>
                <li><code>GET /metrics</code> — Prometheus metrics</li>
            </ul>
            <p><strong>Pipeline:</strong> Pytest → Trivy → Checkov → OPA → cosign → ArgoCD → EKS</p>
        </body>
    </html>
    """
