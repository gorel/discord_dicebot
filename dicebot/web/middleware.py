#!/usr/bin/env python3

from typing import AsyncGenerator

import quart

from dicebot.app import app_sessionmaker
from dicebot.core.client import Client
from dicebot.web import app_ctx, quart_app
from dicebot.web.constants import DISCORD_USER_ID_SESSION_KEY


@quart_app.before_serving
async def create_discord_client() -> None:
    app_ctx.discord_client = await Client.get_and_login()


@quart_app.while_serving
async def with_session() -> AsyncGenerator[None, None]:
    async with app_sessionmaker() as session:
        app_ctx.session = session
        yield


@quart_app.before_request
async def set_current_user() -> None:
    discord_user_id = quart.session.get(DISCORD_USER_ID_SESSION_KEY)
    quart.g.current_user_id = discord_user_id
    if discord_user_id is None:
        quart.g.current_user = None
    else:
        cached = app_ctx.discord_client.get_user(discord_user_id)
        user = cached or await app_ctx.discord_client.fetch_user(discord_user_id)
        quart.g.current_user = user


def register_middleware() -> None:
    """Dummy just so this module is successfully loaded"""
    pass
