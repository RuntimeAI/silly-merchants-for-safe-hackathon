import pytest
from fastapi.testclient import TestClient
from src.api.server import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def sample_strategy():
    """Return a sample strategy for testing"""
    return "Focus on building trust in early rounds and betray in the final round" 