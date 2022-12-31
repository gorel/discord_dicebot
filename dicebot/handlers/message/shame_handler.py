#!/usr/bin/env python3

import logging

import pytz

from dicebot.commands.ban import unban_internal
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler


class ShameHandler(AbstractHandler):
    """If the user is banned, we react SHAME"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return await ctx.author.is_currently_banned(ctx.session, ctx.guild)

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        if ctx.author.is_today_birthday_of_user(pytz.timezone(ctx.guild.timezone)):
            discord_user = await User.get_or_create(ctx.session, ctx.author_id)
            logging.info("It is {ctx.author_id}'s birthday, so we'll unban them")
            await unban_internal(
                ctx, discord_user, "Since it's your birthday, I'm unbanning you early."
            )
        else:
            logging.warning(f"{ctx.author_id} is banned! Shame them.")
            await ctx.message.add_reaction("🇸")
            await ctx.message.add_reaction("🇭")
            await ctx.message.add_reaction("🇦")
            await ctx.message.add_reaction("🇲")
            await ctx.message.add_reaction("🇪")
