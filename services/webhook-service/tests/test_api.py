"""
API tests for the SecurePay Webhook Service.
==============================================
5 focused tests covering:
1. Successful webhook processing
2. Idempotency (duplicate rejection)
3. Invalid amount validation
4. Health endpoint
5. Missing required fields
"""

import pytest


# ──────────────────────────────────────────────────────────────────────
# Test 1: Valid webhook → 200
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_success(client, valid_transaction_payload):
    """A valid transaction webhook should return 200 with confirmation."""
    response = await client.post(
        "/webhook/transaction",
        json=valid_transaction_payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "txn_test_001"
    assert data["merchant_id"] == "merchant_test_001"
    assert float(data["amount"]) == 1500.00
    assert data["status"] == "success"
    assert data["payment_method"] == "upi"
    assert data["message"] == "Webhook processed successfully"
    assert "id" in data  # Internal UUID assigned
    assert "received_at" in data


# ──────────────────────────────────────────────────────────────────────
# Test 2: Duplicate transaction_id → 409
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_duplicate_id(client, valid_transaction_payload):
    """Submitting the same transaction_id twice should return 409 (idempotency)."""
    # First submission — should succeed
    first = await client.post("/webhook/transaction", json=valid_transaction_payload)
    assert first.status_code == 200

    # Second submission — same transaction_id → 409
    second = await client.post("/webhook/transaction", json=valid_transaction_payload)
    assert second.status_code == 409

    detail = second.json()["detail"]
    assert detail["detail"] == "Transaction already processed"
    assert detail["transaction_id"] == "txn_test_001"


# ──────────────────────────────────────────────────────────────────────
# Test 3: Invalid amount (negative) → 422
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_invalid_amount(client, valid_transaction_payload):
    """A negative amount should be rejected with 422 validation error."""
    payload = valid_transaction_payload.copy()
    payload["amount"] = -100.00

    response = await client.post("/webhook/transaction", json=payload)
    assert response.status_code == 422


# ──────────────────────────────────────────────────────────────────────
# Test 4: Health check → 200
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Health check should return 200 with service status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "webhook-service"
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data
    assert data["status"] in ("healthy", "degraded")


# ──────────────────────────────────────────────────────────────────────
# Test 5: Missing required field → 422
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_missing_fields(client):
    """Missing required fields (merchant_id) should return 422."""
    incomplete_payload = {
        "transaction_id": "txn_incomplete",
        # merchant_id is missing
        "amount": 500.00,
        "status": "success",
        "payment_method": "card",
    }

    response = await client.post("/webhook/transaction", json=incomplete_payload)
    assert response.status_code == 422
