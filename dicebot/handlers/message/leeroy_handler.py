#!/usr/bin/env python3


from dicebot.data.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler

DEFAULT_BOT_NAME = "LeeRoy"


class LeeRoyHandler(AbstractHandler):
    """Easter egg if the bot detects its name being said"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        bot_user = ctx.client.user
        bot_name = bot_user.name if bot_user is not None else DEFAULT_BOT_NAME
        return bot_name.lower() in ctx.message.content.lower()

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        await ctx.channel.send("Say that to my face", reference=ctx.message)
