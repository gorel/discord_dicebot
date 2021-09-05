#!/usr/bin/env python3

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

    def __init__(self):
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

    async def handle(
        self,
        client: discord.Client,
        message: discord.Message,
        db_conn: sqlite3.Connection,
    ) -> None:
        guild_id = message.channel.guild.id
        ctx = self.get_or_create_ctx(guild_id)
        await ctx.handle(client, message, db_conn)

    def save(self, filepath: pathlib.Path) -> None:
        with open(filepath, "wb") as f:
            pickle.dump(self.server_files, f)
        for guild_id in self.server_files:
            server = self.servers[guild_id]
            filepath = self.server_files[guild_id]
            server.save()

    @staticmethod
    def load(filepath: pathlib.Path) -> "ServerManager":
        manager = ServerManager()
        with open(filepath, "rb") as f:
            manager.server_files = pickle.load(f)
        for guild_id, filepath in manager.server_files.items():
            manager.servers[guild_id] = ServerContext.load(filepath)
        return manager

    @staticmethod
    def try_load(filepath: pathlib.Path) -> "ServerManager":
        try:
            return ServerManager.load(filepath)
        except Exception:
            return ServerManager()
