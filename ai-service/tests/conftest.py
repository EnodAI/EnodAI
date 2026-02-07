"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_pool():
    """Mock database pool"""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.xreadgroup = AsyncMock(return_value=[])
    client.xadd = AsyncMock(return_value="1234-0")
    client.xack = AsyncMock()
    return client


@pytest.fixture
def sample_metric_data():
    """Sample metric data for testing"""
    return {
        "metric_name": "cpu_usage",
        "metric_value": 85.5,
        "labels": {
            "host": "test-server",
            "environment": "test"
        }
    }


@pytest.fixture
def sample_alert_data():
    """Sample alert data for testing"""
    return {
        "alert_id": 123,
        "payload": {
            "labels": {
                "alertname": "HighCPU",
                "severity": "critical",
                "instance": "server-1"
            },
            "annotations": {
                "description": "CPU usage above 90%",
                "summary": "High CPU detected"
            }
        }
    }


@pytest.fixture
def sample_llm_response():
    """Sample LLM analysis response"""
    return {
        "root_cause": "Memory leak causing CPU spike",
        "mitigation": "Restart the service and monitor memory",
        "analysis": "Critical CPU threshold exceeded"
    }
