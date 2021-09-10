#!/usr/bin/env python3

import enum
import logging
from typing import Awaitable, Callable, List, Optional

import discord

import db_helper
from commands import ban
from message_context import MessageContext
from models import DiscordUser, HandlerStatus, Status, Time


ReactionFunc = Callable[[discord.Reaction, MessageContext], Awaitable[HandlerStatus]]


# TODO: Move this into its own file
async def handle_ban_reaction(
    reaction: discord.Reaction,
    ctx: MessageContext,
) -> HandlerStatus:
    is_ban_emoji = not isinstance(reaction.emoji, str) and reaction.emoji.name == "BAN"
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
    await ban.ban(
        ctx,
        target=DiscordUser(reaction.message.author.id),
        timer=Time("1hr"),
        ban_as_bot=True,
    )
    return HandlerStatus(Status.Success)


DEFAULT_REACTION_HANDLERS = [
    handle_ban_reaction,
]


class ReactionRunner:
    def __init__(self, reaction_handlers: Optional[List[ReactionFunc]] = None) -> None:
        self.handlers = reaction_handlers or DEFAULT_REACTION_HANDLERS

    async def handle_reaction(
        self,
        reaction: discord.Reaction,
        ctx: MessageContext,
    ) -> None:
        logging.info("Called handle_reaction")
        for handler in self.handlers:
            res = await handler(reaction, ctx)
            if res.status is Status.Success:
                logging.info(f"Executed reaction handler {handler.__name__}")
            elif res.status is Status.Failure:
                logging.error(f"Failed reaction handler {handler.__name__}: res.msg")
