#!/usr/bin/env python3

import os

from dicebot.core.constants import DEFAULT_WEB_URL, WEB_URL_KEY
from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@register_command
async def web(ctx: MessageContext) -> None:
    """Return a link to the running webserver"""
    base_url = os.getenv(WEB_URL_KEY, DEFAULT_WEB_URL)
    login_url = f"{base_url}/login"
    await ctx.send(login_url)
