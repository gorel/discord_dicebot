#!/usr/bin/env python3

import asyncio
import logging
import pathlib
import pickle
import sqlite3
from typing import Dict

import discord

from server_context import ServerContext


SERVER_DIRECTORY = pathlib.Path("./server_contexts/")


class ServerManager:
    server_files: Dict[int, pathlib.Path]
    servers: Dict[int, ServerContext]

    def __init__(self, lock: asyncio.Lock, filepath: pathlib.Path) -> None:
        self.lock = lock
        self.filepath = filepath
        self.server_files = {}
        self.servers = {}
        SERVER_DIRECTORY.mkdir(parents=True, exist_ok=True)

    def get_ctx(self, guild_id: int) -> ServerContext:
        return self.servers[guild_id]

    def get_or_create_ctx(self, guild_id: int) -> ServerContext:
        try:
            return self.get_ctx(guild_id)
        except Exception:
            filepath = SERVER_DIRECTORY / str(guild_id)
            ctx = ServerContext(filepath, guild_id)
            self.server_files[guild_id] = filepath
            self.servers[guild_id] = ctx
            return ctx

    async def handle_message(
        self,
        client: discord.Client,
        message: discord.Message,
        db_conn: sqlite3.Connection,
    ) -> None:
        if isinstance(message.channel, discord.DMChannel):
            # Use the DM Channel ID as the guild_id
            # TODO: Rename guild_id to chat_id or something more generic
            channel_id = message.channel.id
            ctx = self.get_or_create_ctx(channel_id)
            await ctx.handle_dm(client, message, db_conn)
        else:
            guild_id = message.channel.guild.id
            ctx = self.get_or_create_ctx(guild_id)
            await ctx.handle_message(client, message, db_conn)

    async def handle_reaction_add(
        self,
        client: discord.Client,
        reaction: discord.Reaction,
        user: discord.User,
        db_conn: sqlite3.Connection,
    ) -> None:
        guild_id = reaction.message.channel.guild.id
        ctx = self.get_or_create_ctx(guild_id)
        await ctx.handle_reaction_add(client, reaction, user, db_conn)

    async def save(self) -> None:
        # When saving, get the *current state* and just update it
        # This is necessary since we may be out of date
        async with self.lock:
            current_state = self.load(self.lock, self.filepath)
            new_servers = current_state.servers.keys() - self.servers.keys()
            logging.info(f"Manager saving after learning of new servers: {new_servers}")
            self.server_files.update(current_state.server_files)
            self.servers.update(current_state.servers)

            with open(self.filepath, "wb") as f:
                pickle.dump(self.server_files, f)

    @staticmethod
    def load(lock: asyncio.Lock, filepath: pathlib.Path) -> "ServerManager":
        manager = ServerManager(lock, filepath)
        with open(filepath, "rb") as f:
            manager.server_files = pickle.load(f)
        for guild_id, filepath in manager.server_files.items():
            manager.servers[guild_id] = ServerContext.load(filepath)
        return manager

    @staticmethod
    def try_load(lock: asyncio.Lock, filepath: pathlib.Path) -> "ServerManager":
        try:
            return ServerManager.load(lock, filepath)
        except Exception:
            return ServerManager(lock, filepath)
