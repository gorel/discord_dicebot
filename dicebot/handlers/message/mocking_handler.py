#!/usr/bin/env python3

import datetime
import random

import pytz
from discord import Embed

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler

SPONGEBOB_IMG_URL = "https://imgflip.com/s/meme/Mocking-Spongebob.jpg"


class MockingHandler(AbstractHandler):
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
        embed = Embed(type="image")
        embed.set_image(url=SPONGEBOB_IMG_URL)
        await ctx.channel.send(self.spongebobify(ctx.message.content), embed=embed)
