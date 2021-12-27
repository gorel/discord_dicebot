#!/usr/bin/env python3

import discord

from message_context import MessageContext


async def add_roll_reminder(ctx: MessageContext) -> None:
    """Remind the user whenever they can roll again"""
    ctx.server_ctx.add_roll_reminder(ctx.discord_id)
    await ctx.channel.send(
        f"Okay, <@{ctx.discord_id}>, I'll DM you when it's time to roll."
    )


async def remove_roll_reminder(ctx: MessageContext) -> None:
    """Remind the user whenever they can roll again"""
    ctx.server_ctx.remove_roll_reminder(ctx.discord_id)
    await ctx.channel.send(
        f"Okay, <@{ctx.discord_id}>, I'll stop DMing you when it's time to roll."
    )


async def send_roll_reminder(ctx: MessageContext, user: discord.User) -> None:
    guild = await ctx.client.fetch_guild(ctx.server_ctx.guild_id)
    guild_name = guild.name
    dm_channel = user.dm_channel
    if dm_channel is None:
        dm_channel = await user.create_dm()
    await dm_channel.send(f"It's time to roll in {guild_name}!")
