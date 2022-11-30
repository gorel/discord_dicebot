#!/usr/bin/env python3


from data_infra.message_context import MessageContext
from on_message_handlers.abstract_handler import AbstractHandler


class BirthdayHandler(AbstractHandler):
    """Give a balloon to someone on their birthday"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return ctx.author.is_today_birthday_of_user(ctx.guild.timezone)

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        await ctx.message.add_reaction("🎈")
