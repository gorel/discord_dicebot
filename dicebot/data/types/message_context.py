#!/usr/bin/env python3

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
import textwrap
from typing import Optional, Any

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User

MAX_CHARS_PER_MSG = 3000


@dataclass
class MessageContext:
    client: discord.Client
    session: AsyncSession
    author: User
    guild: Guild
    discord_guild: Optional[discord.Guild]
    message: discord.Message
    reactor: Optional[User]
    reaction: Optional[discord.Reaction]
    is_test: bool
    # Arbitrary state bag for handlers to communicate
    state: dict[str, Any] = field(default_factory=dict)

    @property
    def guild_id(self) -> int:
        return self.guild.id

    @property
    def author_id(self) -> int:
        return self.author.id

    @property
    def channel(self) -> discord.TextChannel | discord.DMChannel:
        assert isinstance(self.message.channel, discord.TextChannel) or isinstance(
            self.message.channel, discord.DMChannel
        )
        return self.message.channel

    # This function is a simple wrapper around the official send() function and thus does no chunking
    # for messages that are over the length limit.
    async def send(self, *args, silent: bool = True, **kwargs) -> None:
        await self.channel.send(*args, silent=silent, **kwargs)

    # This function contains some special logic to segment messages that are over the length limit.
    async def quote_reply(self, msg: str, silent: bool = True) -> None:
        if len(msg) <= MAX_CHARS_PER_MSG:
            await self.channel.send(msg, reference=self.message, silent=silent)
            return

        for msg_chunk in textwrap.wrap(msg, width=MAX_CHARS_PER_MSG):
            await self.channel.send(msg_chunk, reference=self.message, silent=silent)
            await asyncio.sleep(1)
