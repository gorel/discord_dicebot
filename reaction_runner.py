#!/usr/bin/env python3

import logging
from typing import Awaitable, Callable, List, Optional

import discord

from message_context import MessageContext
from models import HandlerStatus, Status
from reactions import ban, kekw

ReactionFunc = Callable[
    [discord.Reaction, discord.User, MessageContext], Awaitable[HandlerStatus]
]


DEFAULT_REACTION_HANDLERS = [
    ban.handle_ban_reaction,
    kekw.handle_kekw_reaction,
]


class ReactionRunner:
    def __init__(self, reaction_handlers: Optional[List[ReactionFunc]] = None) -> None:
        self.handlers = reaction_handlers or DEFAULT_REACTION_HANDLERS

    async def handle_reaction(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        ctx: MessageContext,
    ) -> None:
        reaction_name: str
        if isinstance(reaction.emoji, str):
            reaction_name = reaction.emoji
        else:
            reaction_name = reaction.emoji.name

        logging.info(f"Called handle_reaction: {reaction_name}")

        for handler in self.handlers:
            res = await handler(reaction, user, ctx)
            if res.status is Status.Success:
                logging.info(f"Executed reaction handler {handler.__name__}")
            elif res.status is Status.Failure:
                logging.error(f"Failed reaction handler {handler.__name__}: {res.msg}")
