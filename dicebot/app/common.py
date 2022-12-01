#!/usr/bin/env python3

import os

import dotenv
from celery import Celery
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from dicebot.core.client import Client
from dicebot.data.db.base import Base

DEFAULT_DB_URI = "sqlite+aiosqlite:///:memory:"
DEFAULT_BROKER_URL = "redis://localhost:6379"
DEFAULT_RESULT_BACKEND = "redis://localhost:6379"
TASKS_DIR = "dicebot.data.tasks"


# Load environment
dotenv.load_dotenv()
db_uri = os.getenv("DB_URI", DEFAULT_DB_URI)
discord_token = os.getenv("DISCORD_TOKEN", "")
test_guild_id = int(os.getenv("TEST_GUILD_ID", 0)) or None
broker_url = os.getenv("CELERY_BROKER_URL", DEFAULT_BROKER_URL)
result_backend = os.getenv("CELERY_RESULT_BACKEND", DEFAULT_RESULT_BACKEND)


engine = create_async_engine(db_uri)

async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

client = Client(async_sessionmaker, test_guild_id=test_guild_id)

celery_app = Celery(
    "dicebot",
    broker=broker_url,
    backend=result_backend,
    include=[TASKS_DIR],
    namespace="CELERY",
)


async def create_all() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
