from fastapi import Depends, FastAPI
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from app.db import get_session, init_db
from app.models import Song, SongCreate
from fastapi import HTTPException


app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/ping")
async def pong():
    return {"ping": "pong!"}

@app.get("/songs", response_model=list[Song])
async def get_songs(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Song))
    songs = result.scalars().all()
    return [Song(name=song.name, artist=song.artist, year=song.year, id=song.id) for song in songs]

@app.get("/songs/{song_id}", response_model=Song)
async def get_song(song_id: int, session: AsyncSession = Depends(get_session)):
    song = await session.get(Song, song_id)
    if song:
        return Song(name=song.name, artist=song.artist, year=song.year, id=song.id)
    raise HTTPException(status_code=404, detail="Song not found")

@app.post("/songs")
async def add_songs(songs: List[SongCreate], session: AsyncSession = Depends(get_session)):
    new_songs = [Song(**song.dict()) for song in songs]
    session.add_all(new_songs)
    await session.commit()
    for song in new_songs:
        await session.refresh(song)
    return new_songs

@app.put("/update/{song_id}")
async def update_song(song_id: int, song_data: SongCreate, session: AsyncSession = Depends(get_session)):
    song = await session.get(Song, song_id)
    if song:
        for key, value in song_data.dict().items():
            setattr(song, key, value)
        await session.commit()
        await session.refresh(song)
        return song
    return {"message": "Song not found"}, 404

@app.delete("/delete/{song_id}")
async def delete_song(song_id: int, session: AsyncSession = Depends(get_session)):
    song = await session.get(Song, song_id)
    if song:
        await session.delete(song)
        await session.commit()
        return {"message": "Song deleted successfully"}
    return {"message": "Song not found"}, 404
