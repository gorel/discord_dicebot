#!/usr/bin/env python3

from __future__ import annotations

import datetime
import logging
import os
import random
from typing import Optional

import discord
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dicebot.app import app_sessionmaker
from dicebot.core.server_manager import ServerManager
from dicebot.data.db.user import User

TEST_PREFIX = "tt "


class Client(discord.Client):
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        test_guild_id: Optional[int] = None,
    ):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(intents=intents)
        self.is_test = test_guild_id is not None
        self.test_guild_id = test_guild_id
        self.sessionmaker = sessionmaker

    async def on_connect(self) -> None:
        start = datetime.datetime.now(tz=datetime.timezone.utc)
        activities = [
            discord.Game("in the Metaverse", start=start),
            discord.Game("Barbie Horse Adventure", start=start),
            discord.Game("Connect Four", start=start),
            discord.Game("Excel", start=start),
            discord.Game("Fortnite", start=start),
            discord.Game("Minecraft", start=start),
            discord.Game("Neovim", start=start),
            discord.Game("God", start=start),
            discord.Game("charades with Alexa", start=start),
            discord.Game("hide and seek with a Roomba", start=start),
            discord.Game("tag with self-driving cars", start=start),
        ]
        choice = random.choice(activities)
        # If it's December, presence = advent of code
        if start.month == 12:
            choice = discord.Game("Advent of Code", start=start)
        # If it's within a week of April 1, presence = tricks on you
        if (start.month == 3 and start.day >= 25) or (
            start.month == 4 and start.day <= 7
        ):
            choice = discord.Game("tricks on you")
        # Don't set presence in test mode
        if not self.is_test:
            logging.info(f"Setting presence to {choice}")
            await self.change_presence(status=discord.Status.online, activity=choice)

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            # Don't let the bot respond to itself
            return

        if self.is_test:
            guild_id = None
            if message.guild is not None:
                guild_id = message.guild.id

            # Only pay attention to messages in the test guild if one was given
            if self.test_guild_id is not None and guild_id != self.test_guild_id:
                return

            # Test messages are designated with a leading prefix
            if message.content.startswith(TEST_PREFIX):
                message.content = message.content[len(TEST_PREFIX) :]
            else:
                return

        async with self.sessionmaker() as session:
            mgr = ServerManager(session)
            await mgr.handle_message(self, message, self.is_test)

    async def on_reaction_add(
        self,
        reaction: discord.Reaction,
        user: discord.User,
    ) -> None:
        if user == self.user:
            # Don't let the bot listen to reactions from itself
            return

        if self.is_test:
            guild_id = None
            if reaction.message.guild is not None:
                guild_id = reaction.message.guild.id

            # Only pay attention to reactions in the test guild if one was given
            if self.test_guild_id is not None and guild_id != self.test_guild_id:
                return

        async with self.sessionmaker() as session:
            mgr = ServerManager(session)
            await mgr.handle_reaction_add(self, reaction, user, self.is_test)

    async def on_ready(self) -> None:
        assert self.user is not None
        # Ensure our bot is in the db
        async with self.sessionmaker() as session:
            await User.get_or_create(session, self.user.id)

    @classmethod
    async def get_and_login(cls) -> Client:
        """Helper method to get the app default client"""

        test_guild_id = int(os.getenv("TEST_GUILD_ID", 0)) or None
        discord_token = os.getenv("DISCORD_TOKEN", "")

        res = cls(app_sessionmaker, test_guild_id=test_guild_id)
        await res.login(discord_token)

        return res
