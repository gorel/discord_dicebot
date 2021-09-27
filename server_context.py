#!/usr/bin/env python3

import asyncio
import logging
import pathlib
import pickle
import sqlite3
import time
from typing import Any, ClassVar, Dict, Optional

import discord
import pytz

from command_runner import CommandRunner
from message_context import MessageContext
from reaction_runner import ReactionRunner


class ServerContext:
    DEFAULT_CURRENT_ROLL: ClassVar[int] = 6
    DEFAULT_ROLL_TIMEOUT_HOURS: ClassVar[int] = 18

    guild_id: int
    _current_roll: int
    _roll_timeout_hours: int
    _critical_success_msg: str
    _critical_failure_msg: str
    _bans: Dict[int, int]
    _macros: Dict[str, str]
    _tz: str

    def __init__(self, filepath: pathlib.Path, guild_id: int) -> None:
        self.filepath = filepath
        self.guild_id = guild_id
        self._current_roll = ServerContext.DEFAULT_CURRENT_ROLL
        self._roll_timeout_hours = ServerContext.DEFAULT_ROLL_TIMEOUT_HOURS
        self._critical_success_msg = "Critical success!"
        self._critical_failure_msg = "Critical failure!"
        self._bans = {}
        self._macros = {}
        self._tz = "US/Pacific"
        self._ban_reaction_threshold = 2

    # Anything stateful *must* be stored as a property so we can always ensure
    # save is called when it gets updated
    @property
    def current_roll(self) -> int:
        return self._current_roll

    @current_roll.setter
    def current_roll(self, value: int) -> None:
        self._current_roll = value
        self.save()

    @property
    def roll_timeout_hours(self) -> int:
        return self._roll_timeout_hours

    @roll_timeout_hours.setter
    def roll_timeout_hours(self, value: int) -> None:
        self._roll_timeout_hours = value
        self.save()

    @property
    def critical_success_msg(self) -> str:
        return self._critical_success_msg

    @critical_success_msg.setter
    def critical_success_msg(self, value: str) -> None:
        self.critical_success_msg = value
        self.save()

    @property
    def critical_failure_msg(self) -> str:
        return self._critical_failure_msg

    @critical_failure_msg.setter
    def critical_failure_msg(self, value: str) -> None:
        self.critical_failure_msg = value
        self.save()

    @property
    def bans(self) -> Dict[int, int]:
        return self._bans

    @bans.setter
    def bans(self, value: Dict[int, int]) -> None:
        self._bans = value
        self.save()

    def set_ban(self, key: int, value: int) -> None:
        self._bans[key] = value
        self.save()

    @property
    def macros(self) -> Dict[str, str]:
        return self._macros

    @macros.setter
    def macros(self, value: Dict[str, str]) -> None:
        self._macros = value
        self.save()

    def set_macro(self, key: str, value: str) -> None:
        self._macros[key] = value
        self.save()

    def unset_macro(self, key: str) -> None:
        del self._macros[key]
        self.save()

    @property
    def tz(self) -> str:
        # Backwards compatibility
        if getattr(self, "_tz", None) is None:
            self._tz = "US/Pacific"
        return self._tz

    @tz.setter
    def tz(self, value: str) -> None:
        # We let this potentially fail on purpose to bubble up the error
        tz = pytz.timezone(value)
        self._tz = value
        self.save()

    @property
    def ban_reaction_threshold(self) -> int:
        # Backwards compatibility
        if getattr(self, "_ban_reaction_threshold", None) is None:
            self._ban_reaction_threshold = 2
        return self._ban_reaction_threshold

    @ban_reaction_threshold.setter
    def ban_reaction_threshold(self, value: int) -> None:
        self._ban_reaction_threshold = value
        self.save()

    async def handle_message(
        self,
        client: discord.Client,
        message: discord.Message,
        db_conn: sqlite3.Connection,
    ) -> None:
        # TODO: Allow disabling of logging all messages?
        # Don't propagate messages since this is used specifically for logging
        # user messages, which can get spammy
        message_logger = logging.getLogger("messages")
        message_logger.propagate = False

        # Only add the handler *once*
        if len(message_logger.handlers) == 0:
            hdl = logging.StreamHandler()
            hdl.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
            message_logger.addHandler(hdl)

        guild_name = message.guild.name
        username = message.author.name
        # Check the message length is > 0 to ignore logging image-only messages
        if len(message.content) > 0:
            message_logger.info(f"{guild_name} | {username}: {message.content}")

        ctx = MessageContext(
            server_ctx=self, client=client, message=message, db_conn=db_conn,
        )

        runner = CommandRunner()

        # If the user is banned, we react SHAME
        if self.bans.get(ctx.discord_id, -1) > time.time():
            logging.warning(f"{ctx.discord_id} is banned! Shame them.")
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
            else:
                text = self.helptext(runner)
            await ctx.channel.send(text)
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
                logging.exception("Failed to call command")
                await ctx.channel.send(helptext)

    async def handle_reaction_add(
        self,
        client: discord.Client,
        reaction: discord.Reaction,
        user: discord.User,
        db_conn: sqlite3.Connection,
    ) -> None:
        ctx = MessageContext(
            server_ctx=self, client=client, message=reaction.message, db_conn=db_conn,
        )
        runner = ReactionRunner()
        await runner.handle_reaction(reaction, user, ctx)

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
        # When saving, get the *current state* and just update it
        # This is necessary since we may be out of date
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
