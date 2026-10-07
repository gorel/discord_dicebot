#!/usr/bin/env python3

import re

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler

ORB_REGEX = re.compile(r"\bDailyOrbs\b")
COLORS = ["orange", "green", "blue", "purple"]


class OrbTranslatorHandler(AbstractHandler):
    """Translate the DailyOrbs messages into a human-readable format."""

    async def should_handle(self, ctx: MessageContext) -> bool:
        return ORB_REGEX.search(ctx.message.content) is not None

    async def handle(self, ctx: MessageContext) -> None:
        parts = []
        for color in COLORS:
            emoji = f":{color}_circle:"
            n = ctx.message.content.count(emoji)
            parts.append(emoji * n)
        await ctx.quote_reply("\n".join(parts))
