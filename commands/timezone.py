#!/usr/bin/env python3

import datetime

import pytz

import command
from message_context import MessageContext


def localize(unixtime: int, tz: str) -> str:
    dt = datetime.datetime.utcfromtimestamp(unixtime)
    dt_utc = pytz.utc.localize(dt)
    new_tz = pytz.timezone(tz)
    return dt_utc.astimezone(new_tz).strftime("%Y-%m-%d %H:%M:%S %Z")


async def set_tz(ctx: MessageContext, tz: str) -> None:
    if command.has_diceboss_role(ctx.message.author):
        try:
            ctx.server_ctx.tz = tz
            await ctx.channel.send(f"Set this server's timezone to '{tz}'")
        except Exception as e:
            await ctx.channel.send(f"Unknown timezone '{tz}'")
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}."
        )
