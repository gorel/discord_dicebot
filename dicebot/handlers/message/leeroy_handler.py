#!/usr/bin/env python3

import random
import re

from dicebot.commands import giffer
from dicebot.data.types.message_context import MessageContext
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
        pattern = re.compile(rf"\b{bot_name}\b", re.IGNORECASE)
        return pattern.search(ctx.message.content) is not None

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # 50% chance to say the quote, 50% chance to send a gif
        if random.random() < 0.5:
            await ctx.quote_reply("Say that to my face")
        else:
            gif_url = await giffer.get_random_gif_url("Say that to my face")
            if gif_url is not None:
                await ctx.quote_reply(gif_url)
