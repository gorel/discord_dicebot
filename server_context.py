#!/usr/bin/env python3

import datetime
import functools
import logging
import os
import pathlib
import pickle
import random
import sqlite3
import time
from typing import ClassVar, Dict, List, Optional, Set

import dateutil.parser
import discord
import pytz

from command_runner import CommandRunner
from message_context import MessageContext
from reaction_runner import ReactionRunner

LONG_MESSAGE_CHAR_THRESHOLD = 700
LONG_MESSAGE_RESPONSE = "https://user-images.githubusercontent.com/2358378/199403413-b1f903f3-998e-481c-9172-8b323cf746f4.png"


# TODO: Really belongs in the wordle file
@functools.lru_cache
def get_valid_words() -> List[str]:
    words = []
    with open(os.getenv("WORDS_FILE", "")) as f:
        for line in f:
            words.append(line.strip())
    return words


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
    _roll_reminders: Set[int]
    _wordle: str
    _birthdays: Dict[int, str]

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
        self._turbo_ban_timing_threshold = 300
        self._roll_reminders = set()
        self._wordle = ""
        self._birthdays = {}

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
        pytz.timezone(value)
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

    @property
    def turbo_ban_timing_threshold(self) -> int:
        # Backwards compatibility
        if getattr(self, "_turbo_ban_timing_threshold", None) is None:
            # Stored in seconds
            self._turbo_ban_timing_threshold = 300
        return self._turbo_ban_timing_threshold

    @turbo_ban_timing_threshold.setter
    def turbo_ban_timing_threshold(self, value: int) -> None:
        self._turbo_ban_timing_threshold = value
        self.save()

    @property
    def birthdays(self) -> Dict[int, str]:
        # Backwards compatibility
        if getattr(self, "_birthdays", None) is None:
            self._birthdays = {}
        return self._birthdays

    def add_birthday(self, discord_id: int, birthday: str) -> None:
        self.birthdays[discord_id] = birthday
        self.save()

    def is_today_birthday_of(self, discord_id: int) -> bool:
        birthday = self.birthdays.get(discord_id)
        if birthday is None:
            return False

        # If we saved the birthday in an invalid format,
        # we'll get a ParserError here which will break the bot
        try:
            now = datetime.datetime.now()
            target_datetime = dateutil.parser.parse(birthday).replace(year=now.year)
            return target_datetime.date() == now.date()
        except Exception:
            return False

    def add_roll_reminder(self, user_id: int) -> None:
        # Backwards compatibility
        if getattr(self, "_roll_reminders", None) is None:
            self._roll_reminders = set()
        self._roll_reminders.add(user_id)
        self.save()

    def remove_roll_reminder(self, user_id: int) -> None:
        # Backwards compatibility
        if getattr(self, "_roll_reminders", None) is None:
            self._roll_reminders = set()
        if user_id in self._roll_reminders:
            self._roll_reminders.remove(user_id)
            self.save()

    def should_remind(self, user_id: int) -> bool:
        # Backwards compatibility
        if getattr(self, "_roll_reminders", None) is None:
            self._roll_reminders = set()
        return user_id in self._roll_reminders

    def gen_new_wordle(self) -> str:
        words = get_valid_words()
        self._wordle = random.choice(words)
        self.save()
        return self._wordle

    def get_wordle(self) -> str:
        if getattr(self, "_wordle", None) is None:
            self.gen_new_wordle()
        return self._wordle

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
            server_ctx=self, client=client, message=message, db_conn=db_conn
        )

        runner = CommandRunner()

        # TODO: Create a way to hook in generic message handlers
        # instead of all the custom handling logic below hap-hazardly thrown in

        # If the user is banned, we react SHAME
        if self.bans.get(ctx.discord_id, -1) > time.time():
            logging.warning(f"{ctx.discord_id} is banned! Shame them.")
            await message.add_reaction("🇸")
            await message.add_reaction("🇭")
            await message.add_reaction("🇦")
            await message.add_reaction("🇲")
            await message.add_reaction("🇪")

        # If it's the user's birthday, we give them a balloon
        if self.is_today_birthday_of(ctx.discord_id):
            logging.info("Someone's having a birthday! Let's send a balloon.")
            await message.add_reaction("🎈")

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
                logging.exception(f"Failed to call command: {e}")
                await ctx.channel.send(helptext)
        elif len(message.content) > LONG_MESSAGE_CHAR_THRESHOLD:
            await ctx.channel.send(LONG_MESSAGE_RESPONSE)

    async def handle_reaction_add(
        self,
        client: discord.Client,
        reaction: discord.Reaction,
        user: discord.User,
        db_conn: sqlite3.Connection,
    ) -> None:
        ctx = MessageContext(
            server_ctx=self, client=client, message=reaction.message, db_conn=db_conn
        )
        runner = ReactionRunner()
        await runner.handle_reaction(reaction, user, ctx)

    async def handle_dm(
        self,
        client: discord.Client,
        message: discord.Message,
        db_conn: sqlite3.Connection,
    ) -> None:
        # TODO: Only allow certain commands?
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

        username = message.author.name
        # Check the message length is > 0 to ignore logging image-only messages
        if len(message.content) > 0:
            message_logger.info(f"DM from {username}: {message.content}")

        ctx = MessageContext(
            server_ctx=self, client=client, message=message, db_conn=db_conn
        )

        runner = CommandRunner()

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
                logging.exception(f"Failed to call command: {e}")
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
        # When saving, get the *current state* and just update it
        # This is necessary since we may be out of date
        with open(self.filepath, "wb") as f:
            pickle.dump(self, f)

    def reload(self) -> None:
        # It's possible this is a *brand new conversation* that hasn't even
        # been saved yet
        try:
            with open(self.filepath, "rb") as f:
                updated = pickle.load(f)
                # Hacky...
                self.__dict__.update(updated.__dict__)
        except Exception:
            logging.warning(f"Could not reload ctx {self.guild_id}")

    @staticmethod
    def load(filepath: pathlib.Path) -> "ServerContext":
        with open(filepath, "rb") as f:
            return pickle.load(f)
