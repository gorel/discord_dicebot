#!/usr/bin/env python3

import logging
from typing import Awaitable, Callable, List, Optional

import discord

from message_context import MessageContext
from models import DiscordUser, HandlerStatus, Status, Time
from reactions import ban


ReactionFunc = Callable[
    [discord.Reaction, discord.User, MessageContext], Awaitable[HandlerStatus]
]


DEFAULT_REACTION_HANDLERS = [
    ban.handle_ban_reaction,
]


class ReactionRunner:
    def __init__(self, reaction_handlers: Optional[List[ReactionFunc]] = None) -> None:
        self.handlers = reaction_handlers or DEFAULT_REACTION_HANDLERS

    async def handle_reaction(
        self, reaction: discord.Reaction, user: discord.User, ctx: MessageContext,
    ) -> None:
        logging.info("Called handle_reaction")
        for handler in self.handlers:
            res = await handler(reaction, user, ctx)
            if res.status is Status.Success:
                logging.info(f"Executed reaction handler {handler.__name__}")
            elif res.status is Status.Failure:
                logging.error(f"Failed reaction handler {handler.__name__}: res.msg")
