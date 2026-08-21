"""
Pydantic v2 schemas for the webhook service.
Defines request/response models for transaction webhooks.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TransactionStatus(str, Enum):
    """Valid transaction statuses from payment gateway."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Supported payment methods."""
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    QR = "qr"
    POS = "pos"


class TransactionWebhook(BaseModel):
    """
    Incoming transaction webhook payload from payment gateway.
    Mirrors the kind of data SecurePay processes for merchant settlements.
    """
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique transaction identifier from payment gateway",
        examples=["txn_abc123def456"],
    )
    merchant_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Merchant identifier",
        examples=["merchant_001"],
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=12,
        decimal_places=2,
        description="Transaction amount in INR (must be positive)",
        examples=[1500.00],
    )
    currency: str = Field(
        default="INR",
        pattern=r"^[A-Z]{3}$",
        description="ISO 4217 currency code",
    )
    status: TransactionStatus = Field(
        ...,
        description="Transaction status",
    )
    payment_method: PaymentMethod = Field(
        ...,
        description="Payment method used",
    )
    customer_email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Customer email (optional)",
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional transaction metadata",
    )

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, v: str) -> str:
        """Ensure transaction_id doesn't contain dangerous characters."""
        if any(c in v for c in ["<", ">", "'", '"', ";", "&"]):
            raise ValueError("transaction_id contains invalid characters")
        return v.strip()


class TransactionResponse(BaseModel):
    """Response after processing a webhook."""
    id: UUID = Field(default_factory=uuid4)
    transaction_id: str
    merchant_id: str
    amount: Decimal
    currency: str
    status: TransactionStatus
    payment_method: PaymentMethod
    received_at: datetime
    message: str = "Webhook processed successfully"


class DuplicateResponse(BaseModel):
    """Response when a duplicate transaction_id is submitted."""
    detail: str = "Transaction already processed"
    transaction_id: str
    original_received_at: datetime


class HealthResponse(BaseModel):
    """Health check response for K8s probes."""
    status: str = "healthy"
    service: str = "webhook-service"
    version: str = "1.0.0"
    database: str = "connected"
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
