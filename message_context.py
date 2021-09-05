#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
import sqlite3
from typing import TYPE_CHECKING

import discord

# Without the conditional import, we create a circular import that python
# cannot resolve, causing the program to crash on startup
# This is entirely due to providing the rich type hinting below :(
if TYPE_CHECKING:
    from server_context import ServerContext


@dataclasses.dataclass
class MessageContext:
    server_ctx: ServerContext
    client: discord.Client
    message: discord.Message
    db_conn: sqlite3.Connection

    @property
    def channel(self) -> discord.TextChannel:
        return self.message.channel

    @property
    def discord_id(self) -> int:
        return self.message.author.id

    @property
    def guild_id(self) -> int:
        return self.message.guild.id
