#!/usr/bin/env python3

import datetime

import pytz

from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@register_command
async def time(ctx: MessageContext) -> None:
    """Announce the current server time"""
    tz = pytz.timezone(ctx.guild.timezone)
    now = datetime.datetime.now(tz=tz)
    localized_str = now.strftime("%I:%M %p %Z")
    await ctx.channel.send(f"The current time in this server is {localized_str}")
