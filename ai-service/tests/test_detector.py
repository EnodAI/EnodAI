"""
Tests for anomaly detector module
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from app.detector import AnomalyDetector


@pytest.fixture
def detector():
    """Create detector instance with mocked model"""
    with patch('app.detector.IsolationForestWrapper') as mock_model:
        detector = AnomalyDetector()
        detector.model = mock_model.return_value
        return detector


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_normal_value(detector):
    """Test anomaly detection with normal value"""
    # Arrange
    detector.model.predict.return_value = np.array([1])  # 1 = normal
    detector.model.score_samples.return_value = np.array([-0.1])

    metric_data = {
        "metric_value": 50.0
    }

    # Act
    result = await detector.detect(metric_data)

    # Assert
    assert result["is_anomaly"] is False
    assert "anomaly_score" in result
    assert result["model_version"] == "if_v1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_anomaly_value(detector):
    """Test anomaly detection with anomalous value"""
    # Arrange
    detector.model.predict.return_value = np.array([-1])  # -1 = anomaly
    detector.model.score_samples.return_value = np.array([-0.8])

    metric_data = {
        "metric_value": 95.0
    }

    # Act
    result = await detector.detect(metric_data)

    # Assert
    assert result["is_anomaly"] is True
    assert result["anomaly_score"] == -0.8


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_missing_value(detector):
    """Test detection with missing metric value"""
    # Arrange
    metric_data = {}

    # Act
    result = await detector.detect(metric_data)

    # Assert
    assert result["is_anomaly"] is False
    assert "error" in result
    assert result["error"] == "Missing metric_value"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_nan_value(detector):
    """Test detection with NaN value"""
    # Arrange
    metric_data = {
        "metric_value": float('nan')
    }

    # Act
    result = await detector.detect(metric_data)

    # Assert
    assert result["is_anomaly"] is False
    assert "error" in result
    assert result["error"] == "Non-finite value"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_infinite_value(detector):
    """Test detection with infinite value"""
    # Arrange
    metric_data = {
        "metric_value": float('inf')
    }

    # Act
    result = await detector.detect(metric_data)

    # Assert
    assert result["is_anomaly"] is False
    assert "error" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_train_model_success(detector, mock_db_pool):
    """Test model training with valid data"""
    # Arrange
    with patch('app.detector.get_db_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetch = AsyncMock(return_value=[
            {"metric_value": 50.0},
            {"metric_value": 55.0},
            {"metric_value": 60.0}
        ])

        # Act
        await detector.train_model()

        # Assert
        detector.model.train.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_train_model_no_data(detector, mock_db_pool):
    """Test model training with no data"""
    # Arrange
    with patch('app.detector.get_db_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetch = AsyncMock(return_value=[])

        # Act
        await detector.train_model()

        # Assert
        detector.model.train.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_invalid_value_type(detector):
    """Test detection with invalid value type"""
    # Arrange
    metric_data = {
        "metric_value": "not_a_number"
    }

    # Act
    result = await detector.detect(metric_data)

    # Assert
    assert result["is_anomaly"] is False
    assert "error" in result
