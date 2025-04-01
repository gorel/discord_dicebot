#!/usr/bin/env python3

import datetime
import random

import pytz
from discord import Embed
from dicebot.commands import giffer

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler
from dicebot.handlers.message.long_message_handler import LongMessageHandler

SPONGEBOB_IMG_URL = "https://imgflip.com/s/meme/Mocking-Spongebob.jpg"


class FoolHandler(AbstractHandler):
    """Mock a message using sPoNgEbOb TeXt"""

    def spongebobify(self, msg: str) -> str:
        s = msg.lower()
        return "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(s))

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        tz = pytz.timezone(ctx.guild.timezone)
        now = datetime.datetime.now(tz=tz)
        is_april_fools = now.month == 4 and now.day == 1
        return is_april_fools and random.random() < 0.25

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        tz = pytz.timezone(ctx.guild.timezone)
        now = datetime.datetime.now(tz=tz)

        # April Fool's 2023 - mocking spongebob
        if now.year == 2023:
            embed = Embed(type="image")
            embed.set_image(url=SPONGEBOB_IMG_URL)
            await ctx.send(self.spongebobify(ctx.message.content), embed=embed)

        # April Fool's 2024 - random gifs for every message
        if now.year == 2024:
            handlers = await ctx.guild.get_all_reaction_handlers(ctx.session)
            handler = random.choice(handlers)
            gif_url = await giffer.get_random_gif_url(handler.gif_search)
            if gif_url is not None:
                await ctx.quote_reply(gif_url)

        # April Fool's 2025 - tl;dr everything over 10 characters
        if now.year == 2025:
            handler = LongMessageHandler(threshold=10, autotldr=True)
            if await handler.should_handle(ctx):
                return await handler.handle(ctx)
