#!/usr/bin/env python3

from typing import Optional

import discord

import command
from message_context import MessageContext
from models import GreedyStr


async def announce(
    ctx: MessageContext,
    server_id: int,
    channel_name: str,
    message: GreedyStr,
) -> None:
    if command.has_diceboss_role(ctx.message.author):
        guild = ctx.client.get_guild(server_id)
        if guild is None:
            guild = await ctx.client.fetch_guild(server_id)
        if guild is None:
            raise ValueError(f"Could not fetch guild_id {server_id}")

        target_channel = None
        channels = await guild.fetch_channels()
        for channel in channels:
            if channel.name == channel_name:
                target_channel = channel
                # We found our channel - we can break out of the loop now
                break

        if target_channel is None:
            raise ValueError(f"Could not find channel {channel_name} in {guild.name}")
        await target_channel.send(message)
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(
            f"Only a diceboss can command me to send announcements, {insult}."
        )
