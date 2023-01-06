#!/usr/bin/env python3

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.reaction.abstract_reaction_handler import AbstractReactionHandler

ALL_STAR_URL = "https://youtu.be/HLQ1cK9Edhc?t=17"


class ShrekReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "shrek"

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        assert ctx.reaction is not None
        await ctx.quote_reply(ALL_STAR_URL)
