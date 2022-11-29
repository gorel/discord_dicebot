#!/usr/bin/env python3

import asyncio
import logging
import os
import pathlib
import pickle
import sqlite3
from typing import Dict

import discord
from sqlalchemy.ext.asyncio import AsyncConnection

from server_context import ServerContext

SERVER_DIRECTORY = pathlib.Path("./server_contexts/")


class ServerManager:
    def __init__(self, conn: AsyncConnection) -> None:
        self.conn = conn

    def get_or_create_ctx(self, guild_id: int) -> ServerContext:
        # TODO: Load from sqlalchemy
        try:
            return self.get_ctx(guild_id)
        except KeyError:
            filepath = SERVER_DIRECTORY / str(guild_id)
            ctx = ServerContext(filepath, guild_id)
            return ctx

    async def handle_message(
        self,
        client: discord.Client,
        message: discord.Message,
    ) -> None:
        if isinstance(message.channel, discord.DMChannel):
            # Use the DM Channel ID as the guild_id
            # TODO: Rename guild_id to chat_id or something more generic
            channel_id = message.channel.id
            ctx = self.get_or_create_ctx(channel_id)
            await ctx.handle_dm(client, message, self.conn)
        else:
            guild_id = message.channel.guild.id
            ctx = self.get_or_create_ctx(guild_id)
            await ctx.handle_message(client, message, self.conn)

    async def handle_reaction_add(
        self,
        client: discord.Client,
        reaction: discord.Reaction,
        user: discord.User,
    ) -> None:
        guild_id = reaction.message.channel.guild.id
        ctx = self.get_or_create_ctx(guild_id)
        await ctx.handle_reaction_add(client, reaction, user, self.conn)
