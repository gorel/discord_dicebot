#!/usr/bin/env python3

import asyncio
import logging

import discord

import db_helper
from commands import ban
from message_context import MessageContext
from models import HandlerStatus, Status

# TODO: Move this into its own file
async def handle_ban_reaction(
    reaction: discord.Reaction, ctx: MessageContext,
) -> HandlerStatus:
    is_ban_emoji = not isinstance(reaction.emoji, str) and reaction.emoji.name == "BAN"

    # Special feature for people trying to ban the bot itself
    if is_ban_emoji and ctx.client.user == ctx.message.author.id:
        my_name = ctx.client.user.name
        await reaction.message.channel.send(
            f"Who *dares* try to ban the mighty {my_name}?!"
        )
        await ban.ban(
            ctx,
            target=DiscordUser(reaction.author.id),
            timer=Time("1hr"),
            ban_as_bot=True,
        )
        return HandlerStatus(Status.Success)

    # Only ban a user if we've hit the reaction threshold
    # TODO: Make threshold configurable per-server
    if not is_ban_emoji or reaction.count != 2:
        return HandlerStatus(Status.Invalid)

    # Check if this message has been banned before
    banned_before = db_helper.has_message_been_banned(
        ctx.db_conn, reaction.message.guild.id, reaction.message.id
    )
    if banned_before:
        logging.warning("New ban reaction on message but it was banned before.")
        return HandlerStatus(Status.Invalid)

    # We need to record that this message has now been banned
    db_helper.record_banned_message(
        ctx.db_conn, reaction.message.guild.id, reaction.message.id
    )

    await reaction.message.channel.send("Bro", reference=reaction.message)
    # Sleep 3 seconds to build suspense
    await asyncio.sleep(3)
    await ban.ban(
        ctx,
        target=DiscordUser(reaction.message.author.id),
        timer=Time("1hr"),
        ban_as_bot=True,
    )
    return HandlerStatus(Status.Success)
