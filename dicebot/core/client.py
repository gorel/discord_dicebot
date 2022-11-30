#!/usr/bin/env python3

from typing import Optional

import discord
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from dicebot.core.server_manager import ServerManager

TEST_PREFIX = "tt "


class Client(discord.Client):
    def __init__(
        self,
        engine: AsyncEngine,
        is_test: bool = False,
        test_guild_id: Optional[int] = None,
    ):
        super().__init__()
        self.is_test = is_test
        self.test_guild_id = test_guild_id
        self.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

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
            await mgr.handle_message(self, message)

    async def on_reaction_add(
        self,
        reaction: discord.Reaction,
        user: discord.User,
    ) -> None:
        if user == self.user:
            # Don't let the bot listen to reactions from itself
            return

        async with self.sessionmaker() as session:
            mgr = ServerManager(session)
            await mgr.handle_reaction_add(self, reaction, user)
