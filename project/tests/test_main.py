import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock, MagicMock
from httpx._transports.asgi import ASGITransport
from fastapi import HTTPException
from app.main import app
from app.models import Song, SongCreate
from app.db import get_session

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture(autouse=True)
def override_get_session(mock_session):
    app.dependency_overrides[get_session] = lambda: mock_session

song_data = Song(id=1, name="Imagine", artist="John Lennon", year=1971)

@pytest.mark.asyncio
async def test_ping():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}

@pytest.mark.asyncio
async def test_get_songs(mock_session):
    mock_scalars = Mock()
    mock_scalars.all.return_value = [song_data]
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/songs")
    assert response.status_code == 200
    assert response.json() == [song_data.model_dump()]

@pytest.mark.asyncio
async def test_get_song_found(mock_session):
    mock_session.get.return_value = song_data

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/songs/1")
    assert response.status_code == 200
    assert response.json() == song_data.model_dump()

@pytest.mark.asyncio
async def test_get_song_not_found(mock_session):
    mock_session.get.return_value = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/songs/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Song not found"}, 404

@pytest.mark.asyncio
async def test_add_songs(mock_session):
    song_create = SongCreate(name="Imagine", artist="John Lennon", year=1971)
    mock_session.refresh = AsyncMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/songs", json=[song_create.model_dump()])
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Imagine"

@pytest.mark.asyncio
async def test_update_song_found(mock_session):
    song_create = SongCreate(name="Let It Be", artist="The Beatles", year=1970)
    mock_session.get.return_value = song_data
    mock_session.refresh = AsyncMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put("/update/1", json=song_create.model_dump())
    assert response.status_code == 200
    assert response.json()["name"] == "Let It Be"

@pytest.mark.asyncio
async def test_update_song_not_found(mock_session):
    mock_session.get.return_value = None
    song_create = SongCreate(name="Song", artist="Artist", year=2000)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put("/update/99", json=song_create.model_dump())
    assert response.status_code == 200  
    assert response.json() == [{"message": "Song not found"}, 404]

@pytest.mark.asyncio
async def test_delete_song_found(mock_session):
    mock_session.get.return_value = song_data

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/delete/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Song deleted successfully"}

@pytest.mark.asyncio
async def test_delete_song_not_found(mock_session):
    mock_session.get.return_value = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/delete/99")
    assert response.status_code == 200
    assert response.json() == [{"message": "Song not found"}, 404]
