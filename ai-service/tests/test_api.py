"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.fixture
def client():
    """Create test client"""
    with patch('app.database.Database.connect'):
        with patch('app.database.Database.disconnect'):
            from main import app
            return TestClient(app)


@pytest.mark.unit
def test_health_endpoint_success(client):
    """Test health endpoint with healthy database"""
    with patch('app.database.Database.execute', new=AsyncMock()):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ai-service"


@pytest.mark.unit
def test_health_endpoint_database_error(client):
    """Test health endpoint with database error"""
    with patch('app.database.Database.execute', side_effect=Exception("DB error")):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "DB error" in data["detail"]


@pytest.mark.unit
def test_get_latest_analysis_success(client):
    """Test get latest analysis endpoint"""
    mock_results = [
        {
            "id": 1,
            "alert_id": 123,
            "analysis_type": "llm_analysis",
            "model_name": "llama2",
            "analysis_data": '{"root_cause": "Test"}',
            "confidence_score": 0.85,
            "created_at": "2024-02-07T10:00:00"
        }
    ]

    with patch('app.database.Database.fetch', new=AsyncMock(return_value=mock_results)):
        response = client.get("/api/v1/analysis/latest")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["analysis_type"] == "llm_analysis"


@pytest.mark.unit
def test_get_latest_analysis_empty(client):
    """Test get latest analysis with no results"""
    with patch('app.database.Database.fetch', new=AsyncMock(return_value=[])):
        response = client.get("/api/v1/analysis/latest")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.unit
def test_get_latest_analysis_database_error(client):
    """Test get latest analysis with database error"""
    with patch('app.database.Database.fetch', side_effect=Exception("DB error")):
        response = client.get("/api/v1/analysis/latest")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
