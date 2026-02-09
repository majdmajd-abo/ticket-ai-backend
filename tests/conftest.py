import os
import sys
import importlib
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so "import app.main" works
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture()
def client(monkeypatch):
    # Set env vars for the app BEFORE importing it
    monkeypatch.setenv("SERVICE_API_KEY", "test-service-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")  # not used because we mock, but must exist
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")

    import app.main as main
    importlib.reload(main)

    return TestClient(main.app)

