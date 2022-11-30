#!/usr/bin/env python3

import pytz

from dicebot.data.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler


class BirthdayHandler(AbstractHandler):
    """Give a balloon to someone on their birthday"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return ctx.author.is_today_birthday_of_user(pytz.timezone(ctx.guild.timezone))

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        await ctx.message.add_reaction("🎈")
