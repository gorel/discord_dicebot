#!/usr/bin/env python3

import asyncio
import datetime
import logging

import discord

import db_helper
from message_context import MessageContext
from models import DiscordUser, HandlerStatus, Status, Time


async def handle_kekw_reaction(
    reaction: discord.Reaction,
    user: discord.User,
    ctx: MessageContext,
) -> HandlerStatus:
    is_kekw_emoji = (
        not isinstance(reaction.emoji, str) and reaction.emoji.name.lower() == "kekw"
    )

    # TODO: This logic could be generalized
    # should_handle could check for proper emoji, no repeat, at threshold, etc
    if not is_kekw_emoji:
        return HandlerStatus(Status.Invalid)

    # Pyre doesn't realize this can't be a string now
    assert not isinstance(reaction.emoji, str)

    # Check if this message has been kekw'd before
    kekwd_before = db_helper.has_message_been_reacted(
        ctx.db_conn, reaction.message.guild.id, reaction.message.id, reaction.emoji.id
    )
    if kekwd_before:
        logging.warning("New kekw reaction on message but it was kekwd before.")
        return HandlerStatus(Status.Invalid)

    # Only send kekw if we've hit the reaction threshold
    if reaction.count != ctx.server_ctx.reaction_threshold:
        return HandlerStatus(Status.Invalid)

    # We need to record that this message has now been kekwd
    db_helper.record_reacted_message(
        ctx.db_conn, reaction.message.guild.id, reaction.message.id, reaction.emoji.id
    )

    # This is the easiest way to pull the same kekw emoji
    emojis = {e.name.lower(): f"<:{e.name}:{e.id}>" for e in ctx.client.emojis}
    await reaction.message.channel.send(
        emojis[reaction.emoji.name.lower()], reference=reaction.message
    )
    return HandlerStatus(Status.Success)
