#!/usr/bin/env python3

import re
from dicebot.handlers.message.abstract_handler import AbstractHandler
from dicebot.data.types.message_context import MessageContext

THANKS_REGEX = re.compile(r"\bthanks\b", re.IGNORECASE)

class ThanksNudgeHandler(AbstractHandler):
    """Nudge users to use !thanks when they say thanks in chat."""

    async def should_handle(self, ctx: MessageContext) -> bool:
        content = ctx.message.content
        if not content:
            return False
        # Ignore commands
        if content.startswith("!"):
            return False
        # Only in guild channels
        if ctx.message.guild is None:
            return False
        return bool(THANKS_REGEX.search(content))

    async def handle(self, ctx: MessageContext) -> None:
        user_mention = ctx.author.as_mention()
        await ctx.send(f"{user_mention} Please use `!thanks` to publicly record your thanks!")