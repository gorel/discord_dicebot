#!/usr/bin/env python3

from message_context import MessageContext
from models import GreedyStr


async def birthday(ctx: MessageContext, birthday: GreedyStr) -> None:
    """Remember a user's birthday so we can wish them a happy birthday later"""
    ctx.server_ctx.birthdays[ctx.discord_id] = birthday
    await ctx.channel.send("Okay, I'll remember your birthday for later!")
