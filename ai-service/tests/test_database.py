"""
Tests for database module
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.database import Database, DatabasePool, get_db_pool


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_connect():
    """Test database connection"""
    with patch('app.database.DatabasePool.get_pool') as mock_get_pool:
        mock_get_pool.return_value = AsyncMock()

        await Database.connect()

        mock_get_pool.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_disconnect():
    """Test database disconnection"""
    with patch('app.database.DatabasePool.close_pool') as mock_close:
        mock_close.return_value = AsyncMock()

        await Database.disconnect()

        mock_close.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_fetch(mock_db_pool):
    """Test fetch operation"""
    # Arrange
    with patch('app.database.DatabasePool.get_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetch = AsyncMock(return_value=[
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"}
        ])

        # Act
        result = await Database.fetch("SELECT * FROM test")

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1
        mock_conn.fetch.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_fetchrow(mock_db_pool):
    """Test fetchrow operation"""
    # Arrange
    with patch('app.database.DatabasePool.get_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetchrow = AsyncMock(return_value={"id": 1, "name": "test"})

        # Act
        result = await Database.fetchrow("SELECT * FROM test WHERE id = $1", 1)

        # Assert
        assert result["id"] == 1
        assert result["name"] == "test"
        mock_conn.fetchrow.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_fetchrow_no_result(mock_db_pool):
    """Test fetchrow with no result"""
    # Arrange
    with patch('app.database.DatabasePool.get_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetchrow = AsyncMock(return_value=None)

        # Act
        result = await Database.fetchrow("SELECT * FROM test WHERE id = $1", 999)

        # Assert
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_fetchval(mock_db_pool):
    """Test fetchval operation"""
    # Arrange
    with patch('app.database.DatabasePool.get_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetchval = AsyncMock(return_value=42)

        # Act
        result = await Database.fetchval("SELECT COUNT(*) FROM test")

        # Assert
        assert result == 42


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_execute(mock_db_pool):
    """Test execute operation"""
    # Arrange
    with patch('app.database.DatabasePool.get_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

        # Act
        result = await Database.execute("INSERT INTO test (name) VALUES ($1)", "test")

        # Assert
        assert result == "INSERT 0 1"
        mock_conn.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_executemany(mock_db_pool):
    """Test executemany operation"""
    # Arrange
    with patch('app.database.DatabasePool.get_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.executemany = AsyncMock()

        data = [("test1",), ("test2",), ("test3",)]

        # Act
        await Database.executemany("INSERT INTO test (name) VALUES ($1)", data)

        # Assert
        mock_conn.executemany.assert_called_once_with(
            "INSERT INTO test (name) VALUES ($1)",
            data
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_fetch_error(mock_db_pool):
    """Test fetch with database error"""
    # Arrange
    with patch('app.database.DatabasePool.get_pool', return_value=mock_db_pool):
        mock_conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        mock_conn.fetch = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await Database.fetch("SELECT * FROM test")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_db_pool():
    """Test get_db_pool helper function"""
    with patch('app.database.DatabasePool.get_pool') as mock_get_pool:
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        result = await get_db_pool()

        assert result == mock_pool
        mock_get_pool.assert_called_once()
