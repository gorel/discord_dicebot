#!/usr/bin/env python3

import logging
from enum import Enum, auto

from data_infra.message_context import MessageContext
from on_message_handlers.abstract_handler import AbstractHandler


class LogMessageHandlerSource(Enum):
    GUILD = auto()
    DM = auto()


class LogMessageHandler(AbstractHandler):
    """Log all messages to console"""

    def __init__(
        self, source: LogMessageHandlerSource = LogMessageHandlerSource.GUILD
    ) -> None:
        self.source = source

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return len(ctx.message.content) > 0

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # TODO: Allow disabling of logging all messages?
        # Don't propagate messages since this is used specifically for logging
        # user messages, which can get spammy
        message_logger = logging.getLogger("messages")
        message_logger.propagate = False

        # Only add the handler *once*
        if len(message_logger.handlers) == 0:
            hdl = logging.StreamHandler()
            hdl.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
            message_logger.addHandler(hdl)

        if self.source is LogMessageHandlerSource.GUILD:
            guild_name = ctx.message.guild.name
            username = ctx.message.author.name
            message_logger.info(f"{guild_name} | {username}: {ctx.message.content}")
        else:
            username = ctx.message.author.name
            message_logger.info(f"DM from {username}: {ctx.message.content}")
