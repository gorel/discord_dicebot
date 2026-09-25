#!/usr/bin/env python3

import re

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler

QUOTES_ONLY_CHANNEL_NAME = "quotes-only"
QUOTES_ONLY_IMAGE_URL = "https://raw.githubusercontent.com/gorel/discord_dicebot/refs/heads/main/dicebot/assets/quotes_only.png"
QUOTE_PAIR_REGEX = re.compile(r'["“”].*["“”]', re.DOTALL)


class QuotesOnlyHandler(AbstractHandler):
    """Scold users who post non-quotes in the quotes-only channel"""

    async def should_handle(self, ctx: MessageContext) -> bool:
        if getattr(ctx.message.channel, "name", None) != QUOTES_ONLY_CHANNEL_NAME:
            return False
        return QUOTE_PAIR_REGEX.search(ctx.message.content) is None

    async def handle(self, ctx: MessageContext) -> None:
        await ctx.quote_reply(QUOTES_ONLY_IMAGE_URL)
