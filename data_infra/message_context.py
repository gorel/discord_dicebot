#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from data_infra.db_models import DiscordUser, Guild


@dataclass
class MessageContext:
    client: discord.Client
    session: AsyncSession
    author: DiscordUser
    guild: Guild
    message: discord.Message
    reactor: Optional[DiscordUser]
    reaction: Optional[discord.Reaction]

    @property
    def guild_id(self) -> int:
        return self.guild.guild_id

    @property
    def author_id(self) -> int:
        return self.author.discord_id

    @property
    def channel(self) -> discord.TextChannel | discord.DMChannel:
        assert isinstance(self.message.channel, discord.TextChannel) or isinstance(
            self.message.channel, discord.DMChannel
        )
        return self.message.channel
