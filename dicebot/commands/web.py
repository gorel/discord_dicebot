#!/usr/bin/env python3

import os

from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext

DEFAULT_WEB_URL = "localhost"
WEB_URL_KEY = "DICEBOT_WEB_URL"


@register_command
async def web(ctx: MessageContext) -> None:
    """Return a link to the running webserver"""
    url = os.getenv(WEB_URL_KEY, DEFAULT_WEB_URL)
    await ctx.channel.send(url)
