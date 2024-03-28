#!/usr/bin/env python3

import logging

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext

# on_message handlers
from dicebot.handlers.message.ban_handler import BanHandler
from dicebot.handlers.message.birthday_handler import BirthdayHandler
from dicebot.handlers.message.command_handler import CommandHandler
from dicebot.handlers.message.fool_handler import FoolHandler
from dicebot.handlers.message.hbd_handler import HbdHandler
from dicebot.handlers.message.leeroy_handler import LeeRoyHandler
from dicebot.handlers.message.log_message_handler import (
    LogMessageHandler,
    LogMessageHandlerSource,
)
from dicebot.handlers.message.long_message_handler import LongMessageHandler
from dicebot.handlers.message.shame_handler import ShameHandler
from dicebot.handlers.message.tldrwl_handler import TldrwlHandler
from dicebot.handlers.message.youtube_handler import YoutubeHandler

# on_reaction handlers
from dicebot.handlers.reaction.ban_handler import BanReactionHandler
from dicebot.handlers.reaction.generic_gif_handler import GenericGifReactionHandler
from dicebot.handlers.reaction.kekw_handler import KekwReactionHandler
from dicebot.handlers.reaction.shrek_handler import ShrekReactionHandler


class GuildContext:
    def __init__(
        self, client: discord.Client, guild: Guild, session: AsyncSession
    ) -> None:
        self.client = client
        self.guild = guild
        self.session = session

    async def handle_message(
        self,
        message: discord.Message,
        is_test: bool,
    ) -> None:
        author = await User.get_or_create(self.session, message.author.id)
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=author,
            guild=self.guild,
            discord_guild=message.guild,
            message=message,
            reactor=None,
            reaction=None,
            is_test=is_test,
        )

        # TODO: Build handlers from set of handlers defined on guild features
        handlers = [
            # NOTE: Explicitly run the LogMessageHandler first
            LogMessageHandler(),
            BanHandler(),
            BirthdayHandler(),
            CommandHandler(),
            HbdHandler(),
            LeeRoyHandler(),
            LongMessageHandler(),
            FoolHandler(),
            ShameHandler(),
            YoutubeHandler(),
            # This can be slow, so keep it at the end of the list
            TldrwlHandler(),
        ]

        for handler in handlers:
            if await handler.should_handle_no_throw(ctx):
                logging.debug(f"Running handler: {handler.__class__.__name__}")
                await handler.handle_no_throw(ctx)

    async def handle_reaction_add(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        is_test: bool,
    ) -> None:
        author = await User.get_or_create(self.session, reaction.message.author.id)
        reactor = await User.get_or_create(self.session, user.id)
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=author,
            guild=self.guild,
            discord_guild=reaction.message.guild,
            message=reaction.message,
            reactor=reactor,
            reaction=reaction,
            is_test=is_test,
        )

        # TODO: Build handlers from set of handlers defined on guild features
        handlers = [
            BanReactionHandler(),
            GenericGifReactionHandler(),
            KekwReactionHandler(),
            ShrekReactionHandler(),
        ]
        for handler in handlers:
            await handler.handle_and_record_no_throw(ctx)

    async def handle_dm(
        self,
        message: discord.Message,
        is_test: bool,
    ) -> None:
        author = await User.get_or_create(self.session, message.author.id)
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=author,
            guild=self.guild,
            discord_guild=message.guild,
            message=message,
            reactor=None,
            reaction=None,
            is_test=is_test,
        )

        # TODO: Build handlers from set of handlers defined on guild features
        handlers = [
            # NOTE: Explicitly run the LogMessageHandler first
            LogMessageHandler(source=LogMessageHandlerSource.DM),
            CommandHandler(),
        ]

        for handler in handlers:
            if await handler.should_handle_no_throw(ctx):
                await handler.handle_no_throw(ctx)
