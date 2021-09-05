#!/usr/bin/env python3

import asyncio
import logging
import pathlib
import pickle
import sqlite3
import time
from typing import Any, ClassVar, Dict, Optional

import discord

from command_runner import CommandRunner
from message_context import MessageContext


class ServerContext:
    DEFAULT_CURRENT_ROLL: ClassVar[int] = 6
    DEFAULT_ROLL_TIMEOUT_HOURS: ClassVar[int] = 18

    guild_id: int
    current_roll: int
    roll_timeout: int
    critical_success_msg: str
    critical_failure_msg: str
    bans: Dict[int, int]
    macros: Dict[str, str]

    def __init__(self, filepath: pathlib.Path, guild_id: int):
        self.filepath = filepath
        self.guild_id = guild_id
        self.current_roll = ServerContext.DEFAULT_CURRENT_ROLL
        self.roll_timeout_hours = ServerContext.DEFAULT_ROLL_TIMEOUT_HOURS
        self.critical_success_msg = ""
        self.critical_failure_msg = ""
        self.bans = {}
        self.macros = {}

    async def handle(
        self,
        client: discord.Client,
        message: discord.Message,
        db_conn: sqlite3.Connection,
    ) -> None:
        ctx = MessageContext(
            server_ctx=self,
            client=client,
            message=message,
            db_conn=db_conn,
        )

        runner = CommandRunner(self)

        # If the user is banned, we react SHAME
        if self.bans.get(ctx.discord_id, -1) > time.time():
            logging.info(f"{ctx.discord_id} is banned! Shame them.")
            await message.add_reaction("🇸")
            await message.add_reaction("🇭")
            await message.add_reaction("🇦")
            await message.add_reaction("🇲")
            await message.add_reaction("🇪")

        # Special handling for !help
        if message.content.startswith("!help"):
            if " " in message.content:
                func = message.content.split(" ")[1]
                text = self.helptext(runner, func)
        elif message.content.startswith("!"):
            # Defer to the command runner
            try:
                await runner.call(ctx)
            except Exception as e:
                end = len(message.content)
                if " " in message.content:
                    end = message.content.index(" ")
                func = message.content[1:end]
                helptext = self.helptext(runner, func)
                await ctx.channel.send(helptext)

    @staticmethod
    def helptext(runner: CommandRunner, cmd: Optional[str] = None) -> str:
        if cmd is not None:
            # Looking for a specific kind of help
            if cmd in runner.cmds:
                cmd_text = runner.helptext(runner.cmds[cmd])
            else:
                cmd_text = f"Could not find command '{cmd}'"
            return cmd_text
        else:
            # Print help on *all* commands
            cmds = [
                # Each line should be relatively short
                runner.helptext(cmd, limit=120)
                for cmd in runner.cmds.values()
            ]
            cmd_text = "**Commands:**\n"
            for cmd in cmds:
                cmd_text += f"\t{cmd}\n"

        return cmd_text

    def save(self) -> None:
        with open(self.filepath, "wb") as f:
            pickle.dump(self, f)


    def reload(self) -> None:
        with open(self.filepath, "rb") as f:
            updated = pickle.load(f)
            # Hacky...
            self.__dict__.update(updated.__dict__)

    @staticmethod
    def load(filepath: pathlib.Path) -> "ServerContext":
        with open(filepath, "rb") as f:
            return pickle.load(f)
