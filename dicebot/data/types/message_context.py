#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User


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

    async def quote_reply(self, msg: str) -> None:
        await self.channel.send(msg, reference=self.message)
