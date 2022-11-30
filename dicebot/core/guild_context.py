#!/usr/bin/env python3

import logging

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db_models import DiscordUser, Guild
from dicebot.data.message_context import MessageContext
# on_message handlers
from dicebot.handlers.message.ban_handler import BanHandler
from dicebot.handlers.message.birthday_handler import BirthdayHandler
from dicebot.handlers.message.command_handler import CommandHandler
from dicebot.handlers.message.leeroy_handler import LeeRoyHandler
from dicebot.handlers.message.log_message_handler import (
    LogMessageHandler, LogMessageHandlerSource)
from dicebot.handlers.message.long_message_handler import LongMessageHandler
from dicebot.handlers.message.shame_handler import ShameHandler
from dicebot.handlers.message.youtube_handler import YoutubeHandler
# on_reaction handlers
from dicebot.handlers.reaction.ban_handler import BanReactionHandler
from dicebot.handlers.reaction.kekw_handler import KekwReactionHandler


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
        author = await DiscordUser.get_or_create(self.session, message.author.id)
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=author,
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
        author = await DiscordUser.get_or_create(
            self.session, reaction.message.author.id
        )
        reactor = await DiscordUser.get_or_create(self.session, user.id)
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=author,
            guild=self.guild,
            message=reaction.message,
            reactor=reactor,
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
        author = await DiscordUser.get_or_create(self.session, message.author.id)
        ctx = MessageContext(
            client=self.client,
            session=self.session,
            author=author,
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
