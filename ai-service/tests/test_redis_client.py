"""
Tests for Redis client and consumer
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.redis_client import RedisClient, RedisConsumer


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_client_connect():
    """Test Redis client connection"""
    with patch('app.redis_client.redis.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.xgroup_create = AsyncMock()
        mock_from_url.return_value = mock_redis

        client = RedisClient()
        await client.connect()

        mock_redis.ping.assert_called_once()
        mock_redis.xgroup_create.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_client_consume_success(mock_redis_client):
    """Test successful message consumption"""
    # Arrange
    client = RedisClient()
    client.redis = mock_redis_client

    mock_redis_client.xreadgroup = AsyncMock(return_value=[
        ("metrics:raw", [("1234-0", {"type": "metric", "data": "{}"})])
    ])

    # Act
    messages = await client.consume()

    # Assert
    assert len(messages) == 1
    mock_redis_client.xreadgroup.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_client_consume_no_messages(mock_redis_client):
    """Test consumption with no messages"""
    # Arrange
    client = RedisClient()
    client.redis = mock_redis_client

    mock_redis_client.xreadgroup = AsyncMock(return_value=[])

    # Act
    messages = await client.consume()

    # Assert
    assert len(messages) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_client_consume_connection_error():
    """Test consumption with connection error"""
    # Arrange
    from redis.exceptions import ConnectionError

    client = RedisClient()
    mock_redis = AsyncMock()
    mock_redis.xreadgroup = AsyncMock(side_effect=ConnectionError("Connection lost"))
    client.redis = mock_redis

    # Act
    messages = await client.consume()

    # Assert
    assert messages == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_client_ack(mock_redis_client):
    """Test message acknowledgment"""
    # Arrange
    client = RedisClient()
    client.redis = mock_redis_client

    # Act
    await client.ack("1234-0")

    # Assert
    mock_redis_client.xack.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_client_close(mock_redis_client):
    """Test Redis client close"""
    # Arrange
    client = RedisClient()
    client.redis = mock_redis_client

    # Act
    await client.close()

    # Assert
    mock_redis_client.close.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_consumer_process_metric(sample_metric_data, mock_db_pool):
    """Test consumer processing metric message"""
    # Arrange
    consumer = RedisConsumer()

    mock_detector = MagicMock()
    mock_detector.detect = AsyncMock(return_value={
        "is_anomaly": True,
        "anomaly_score": -0.8,
        "model_version": "if_v1"
    })

    mock_llm = MagicMock()

    with patch('app.redis_client.get_db_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.execute = AsyncMock()

        # Act
        await consumer._process_message(
            "1234-0",
            {
                "type": "metric",
                "data": json.dumps(sample_metric_data)
            },
            mock_detector,
            mock_llm
        )

        # Assert
        mock_detector.detect.assert_called_once()
        mock_conn.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_consumer_process_alert(sample_alert_data, sample_llm_response, mock_db_pool):
    """Test consumer processing alert message"""
    # Arrange
    consumer = RedisConsumer()

    mock_detector = MagicMock()

    mock_llm = MagicMock()
    mock_llm.analyze = AsyncMock(return_value=sample_llm_response)

    with patch('app.redis_client.get_db_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.execute = AsyncMock()

        # Act
        await consumer._process_message(
            "1234-0",
            {
                "type": "alert",
                "data": json.dumps(sample_alert_data)
            },
            mock_detector,
            mock_llm
        )

        # Assert
        mock_llm.analyze.assert_called_once()
        mock_conn.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_consumer_process_unknown_type():
    """Test consumer with unknown message type"""
    # Arrange
    consumer = RedisConsumer()
    mock_detector = MagicMock()
    mock_llm = MagicMock()

    # Act & Assert (should not raise)
    await consumer._process_message(
        "1234-0",
        {
            "type": "unknown",
            "data": "{}"
        },
        mock_detector,
        mock_llm
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_consumer_process_invalid_json():
    """Test consumer with invalid JSON data"""
    # Arrange
    consumer = RedisConsumer()
    mock_detector = MagicMock()
    mock_llm = MagicMock()

    # Act & Assert (should not raise)
    await consumer._process_message(
        "1234-0",
        {
            "type": "metric",
            "data": "invalid json"
        },
        mock_detector,
        mock_llm
    )


@pytest.mark.unit
def test_redis_consumer_stop():
    """Test consumer stop"""
    # Arrange
    consumer = RedisConsumer()
    consumer.running = True

    # Act
    import asyncio
    asyncio.run(consumer.stop())

    # Assert
    assert consumer.running is False
