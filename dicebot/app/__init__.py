#!/usr/bin/env python3

import os

import dotenv
from celery import Celery
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from dicebot.app.defaults import (
    DEFAULT_BROKER_URL,
    DEFAULT_DB_URI,
    DEFAULT_RESULT_BACKEND,
    TASKS_DIR,
)

# Load environment
dotenv.load_dotenv()
__db_uri = os.getenv("DB_URI", DEFAULT_DB_URI)
__broker_url = os.getenv("CELERY_BROKER_URL", DEFAULT_BROKER_URL)
__result_backend = os.getenv("CELERY_RESULT_BACKEND", DEFAULT_RESULT_BACKEND)


# Objects/variables we intend to export go below here
discord_token = os.getenv("DISCORD_TOKEN", "")

engine = create_async_engine(__db_uri)

app_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

celery_app = Celery(
    "dicebot",
    broker=__broker_url,
    backend=__result_backend,
    include=[TASKS_DIR],
    namespace="CELERY",
)
