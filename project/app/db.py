import os
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine: AsyncEngine | None = None
if DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) if engine else None

async def get_session() -> AsyncSession:
    if not async_session:
        raise RuntimeError("async_session is not initialized. Possibly running in test mode without engine.")
    async with async_session() as session:
        yield session

async def init_db():
    if not engine:
        raise RuntimeError("Engine not initialized.")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)