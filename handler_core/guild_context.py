#!/usr/bin/env python3

import logging

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from data_infra.db_models import DiscordUser, Guild
from data_infra.message_context import MessageContext
# on_message handlers
from on_message_handlers.ban_handler import BanHandler
from on_message_handlers.birthday_handler import BirthdayHandler
from on_message_handlers.command_handler import CommandHandler
from on_message_handlers.leeroy_handler import LeeRoyHandler
from on_message_handlers.log_message_handler import (LogMessageHandler,
                                                     LogMessageHandlerSource)
from on_message_handlers.long_message_handler import LongMessageHandler
from on_message_handlers.shame_handler import ShameHandler
from on_message_handlers.youtube_handler import YoutubeHandler
# on_reaction handlers
from on_reaction_handlers.ban_handler import BanReactionHandler
from on_reaction_handlers.kekw_handler import KekwReactionHandler


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
    ) -> None:
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=DiscordUser.get_or_create(message.author.id),
            guild=self.guild,
            message=message,
            reactor=None,
            reaction=None,
        )

        # TODO: Build handlers from set of handlers defined on guild features
        handlers = [
            # NOTE: Explicitly run the LogMessageHandler first
            LogMessageHandler(),
            BanHandler(),
            BirthdayHandler(),
            CommandHandler(),
            LeeRoyHandler(),
            LongMessageHandler(),
            ShameHandler(),
            YoutubeHandler(),
        ]

        for handler in handlers:
            if await handler.should_handle_no_throw(ctx):
                logging.info(f"Running handler: {handler.__class__.__name__}")
                await handler.handle_no_throw(ctx)

    async def handle_reaction_add(
        self,
        reaction: discord.Reaction,
        user: discord.User,
    ) -> None:
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=DiscordUser.get_or_create(reaction.message.author.id),
            guild=self.guild,
            message=reaction.message,
            reactor=DiscordUser.get_or_create(user.id),
            reaction=reaction,
        )

        # TODO: Build handlers from set of handlers defined on guild features
        handlers = [BanReactionHandler(), KekwReactionHandler()]
        for handler in handlers:
            await handler.handle_and_record_no_throw(
                ctx,
            )

    async def handle_dm(
        self,
        message: discord.Message,
    ) -> None:
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=DiscordUser.get_or_create(message.author.id),
            guild=self.guild,
            message=message,
            reactor=None,
            reaction=None,
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
