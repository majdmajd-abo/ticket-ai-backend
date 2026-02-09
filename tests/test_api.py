def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_analyze_requires_api_key(client):
    # Use VALID input so we actually reach auth (otherwise schema validation returns 422)
    r = client.post("/analyze", json={"subject": "Hello", "message": "Hello there, this is a test message."})
    assert r.status_code == 401


def test_analyze_success_with_mocked_ai(client, monkeypatch):
    # Mock the AI function so tests don't call OpenAI
    import app.main as main

    def fake_analyze_ticket_with_ai(subject: str, message: str, model: str):
        return {
            "category": "billing",
            "urgency": "high",
            "sentiment": "negative",
            "language": "en",
            "summary": "Customer reports a billing problem.",
            "suggested_reply": (
                "Thanks for reaching out. We’ll look into the duplicate charge. "
                "Please share your invoice ID and the last 4 digits of the card."
            ),
            "tags": ["billing", "refund"],
            "confidence": 0.88,
        }

    monkeypatch.setattr(main, "analyze_ticket_with_ai", fake_analyze_ticket_with_ai)

    headers = {"X-API-Key": "test-service-key"}

    r = client.post(
        "/analyze",
        headers=headers,
        json={"subject": "Charged twice", "message": "I was charged twice, refund please."},
    )

    assert r.status_code == 200
    data = r.json()

    # Basic schema checks
    assert data["category"] in [
        "billing",
        "bug",
        "feature_request",
        "account_access",
        "performance",
        "security",
        "integration",
        "other",
    ]
    assert data["urgency"] in ["low", "medium", "high"]
    assert data["sentiment"] in ["negative", "neutral", "positive"]
    assert data["language"] in ["en", "he", "ar", "other"]
    assert isinstance(data["tags"], list)
    assert 0.0 <= float(data["confidence"]) <= 1.0

    # Middleware should add a request id header
    assert "X-Request-ID" in r.headers
    assert len(r.headers["X-Request-ID"]) > 0


def test_analyze_rejects_wrong_api_key(client):
    # Use VALID input so we actually reach auth
    r = client.post(
        "/analyze",
        headers={"X-API-Key": "wrong"},
        json={"subject": "Hello", "message": "Hello there, this is a test message."},
    )
    assert r.status_code == 401

