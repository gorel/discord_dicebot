#!/usr/bin/env python3

import abc
import asyncio
import datetime
import enum
import functools
import logging
import random
import time
from typing import Any, List, Type, TypeVar, get_type_hints

import discord

import db_helper
from message_context import MessageContext


T = TypeVar("T")


class GreedyStr(str):
    """
    Special type designation for a string which should consume the rest
    of the arguments when parsing a command. Uses type hinting for some
    weird reflection stuff that kind of feels hacky and sketchy.
    """


def get_witty_insult() -> str:
    return random.choice(
        [
            "bucko",
            "cockalorum",
            "glue eater",
            "kid",
            "ninny",
            "pal",
            "scrub",
            "son",
            "wanker",
        ]
    )


def has_diceboss_role(user: discord.Member) -> bool:
    diceboss_rolename = "diceboss"
    return any(role.name == diceboss_rolename for role in user.roles)


async def roll(ctx: MessageContext) -> None:
    """Roll a die for the server based on the current roll"""
    guild_id = ctx.server_ctx.guild_id
    next_roll = ctx.server_ctx.current_roll
    username = ctx.message.author.name

    last_roll_time = db_helper.get_last_roll_time(
        ctx.db_conn, guild_id, ctx.discord_id,
    )
    now = datetime.datetime.now()

    if last_roll_time is not None:
        logging.info(f"{ctx.discord_id} last rolled at {last_roll_time}")

        last_roll_delta = int((now - last_roll_time).total_seconds() // 3600)
        timeout = ctx.server_ctx.roll_timeout_hours
        if last_roll_delta < timeout:
            await ctx.channel.send(
                f"<@{ctx.discord_id}> last rolled at {last_roll_time} ({last_roll_delta} hours ago).\n"
                f"This server only allows rolling once every {timeout} hours.\n"
            )
            ban_time = Time("1hr")
            await ban(ctx, DiscordUser(ctx.discord_id), ban_time, ban_as_bot=True)
            # Bail early - don't allow rolling
            return

    logging.info(
        f"Next roll in server({guild_id}) for {username} is {next_roll}"
    )

    # Finally, actually roll the die
    roll = random.randint(1, next_roll)
    db_helper.record_roll(ctx.db_conn, guild_id, ctx.message.author.id, roll, next_roll)
    await ctx.channel.send(
        f"```# {roll}\nDetails: [d{next_roll} ({roll})]```"
    )
    logging.info(f"{username} rolled a {roll} (d{next_roll})")

    if roll == 1:
        s = ctx.server_ctx.critical_failure_msg
        if s != "":
            await ctx.channel.send(f"<@{ctx.discord_id}>: {s}")
        else:
            await ctx.channel.send(f"<@{ctx.discord_id}>: gets to rename the chat channel!")
    elif roll == next_roll:
        # Increment the current roll
        ctx.server_ctx.current_roll = next_roll + 1
        logging.info(f"Next roll in server({guild_id}) is now {next_roll + 1}")

        s = ctx.server_ctx.critical_success_msg
        if s != "":
            await ctx.channel.send(f"<@{ctx.discord_id}>: {s}")
        else:
            await ctx.channel.send(f"<@{ctx.discord_id}>: gets to rename the server!")


async def scoreboard(ctx: MessageContext) -> None:
    stats = db_helper.get_al_stats(ctx.db_conn, ctx.server_ctx.guild_id)
    sorted_stats = sorted(stats, key=lambda rec: rec["wins"] - rec["losses"])
    msg = "**Stats:**\n"
    for record in sorted_stats:
        user = ctx.client.get_user(record["discord_id"])
        if not user:
            user = await ctx.client.fetch_user(record["discord_id"])

        wins = record["wins"]
        losses = record["losses"]
        attempts = record["attempts"]
        msg += f"\t- {user.name}: {wins} wins, {losses} losses ({attempts} rolls\n"
    await ctx.channel.send(msg)


class SetMessageSubcommand(enum.Enum):
    WIN = 1
    LOSE = 2

    @classmethod
    def from_str(cls, s: str) -> "SetMessageSubcommand":
        if s.strip().lower() == "win":
            return SetMessageSubcommand.WIN
        elif s.strip().lower() == "lose":
            return SetMessageSubcommand.LOSE
        else:
            raise ValueError(f"Could not parse {s} as SetMessageSubcommand")


async def set_msg(
    ctx: MessageContext,
    win_or_lose: SetMessageSubcommand,
    msg: GreedyStr,
) -> None:
    if has_diceboss_role(ctx.message.author):
        if win_or_lose is SetMessageSubcommand.WIN:
            ctx.server_ctx.critical_success_msg = msg
        else:
            ctx.server_ctx.critical_failure_msg = msg
    else:
        insult = get_witty_insult()
        await ctx.channel.send(
           f"You're not a diceboss.\nDon't try that shit again, {insult}.")


class Rename(enum.Enum):
    SERVER = 1
    TEXT_CHAT = 2


async def rename(
    ctx: MessageContext, new_name: GreedyStr
) -> None:
    location = None

    # Check for last loser
    record = db_helper.get_last_loser(ctx.db_conn, ctx.guild_id)
    if record["discord_id"] == ctx.discord_id and record["rename_used"] == 0:
        location = Rename.TEXT_CHAT

    # Check for last winner
    record = db_helper.get_last_winner(ctx.db_conn, ctx.guild_id)
    if record["discord_id"] == ctx.discord_id and record["rename_used"] == 0:
        location = Rename.SERVER

    # Resolve rename request
    if location == Rename.SERVER:
        await ctx.channel.send(f"Setting server name to: {new_name}")
        await ctx.message.guild.edit(name=new_name, reason="Dice roll")
    elif location == Rename.TEXT_CHAT:
        await ctx.channel.send(f"Setting chat name to: {new_name}")
        await ctx.channel.edit(name=new_name, reason="Dice roll")
    else:
        await ctx.channel.send(
            f"I can't let you do that, <@{ctx.discord_id}>\n"
            "This incident will be recorded."
        )


async def reset_roll(ctx: MessageContext, to: int) -> None:
    ctx.server_ctx.current_roll = to
    await ctx.channel.send(f"<@{ctx.discord_id}> set the next roll to {to}")


async def set_timeout(ctx: MessageContext, hours: int) -> None:
    if has_diceboss_role(ctx.message.author):
        ctx.server_ctx.roll_timeout_hours = hours
        await ctx.channel.send(f"<@{ctx.discord_id}> set the roll timeout to {hours} hours")
    else:
        insult = get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}.")


async def clear_stats(ctx: MessageContext) -> None:
    if has_diceboss_role(ctx.message.author):
        db_helper.clear_all(ctx.db_conn, ctx.server_ctx.guild_id)
        ctx.server_ctx.current_roll = ctx.server_ctx.DEFAULT_CURRENT_ROLL
        await ctx.channel.send(
            "All winner/loser stats have been cleared for this server.\n"
            f"The next roll for this server has been reset to {ctx.server_ctx.current_roll}"
        )
    else:
        insult = get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}.")


class Time:
    def __init__(self, s: str) -> None:
        self.s = s

    def __str__(self) -> str:
        return f"{self.s} ({self.seconds} seconds)"

    def __repr__(self) -> str:
        return str(self)

    @property
    def seconds(self) -> int:
        units = {}
        units["s"] = 1
        units["m"] = units["s"] * 60
        units["h"] = units["m"] * 60
        units["d"] = units["h"] * 24
        units["y"] = units["d"] * 365

        seconds = 0
        idx = 0
        while idx < len(self.s):
            builder = 0
            # Get value
            while idx < len(self.s) and self.s[idx].isdigit():
                builder = builder * 10 + int(self.s[idx])
                idx += 1
            # Now get unit
            unit_value = units[self.s[idx]]
            # Consume until end of units or string
            while idx < len(self.s) and not self.s[idx].isdigit():
                idx += 1
            # Add to total
            seconds += builder * unit_value
        return seconds


async def remindme(
    ctx: MessageContext, timer: Time, text: GreedyStr
) -> None:
    await ctx.channel.send(f"Okay, <@{ctx.discord_id}>, I'll remind you in {timer}")
    logging.info(f"Will now sleep for {timer.seconds} seconds for reminder")
    await asyncio.sleep(timer.seconds)
    await ctx.channel.send(f"Reminder for <@{ctx.discord_id}>: {text}")


class DiscordUser:
    def __init__(self, discord_id: int) -> None:
        self.id = discord_id


    def __str__(self) -> str:
        return str(self.id)


    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_str(cls, s: str) -> "DiscordUser":
        if len(s) > 0 and s[0] == "<" and s[-1] == ">":
            s = s[1:-1]
        if len(s) > 0 and s[0:2] == "@!":
            s = s[2:]
        return DiscordUser(int(s))


async def ban(
        ctx: MessageContext,
        target: DiscordUser,
        timer: Time,
        ban_as_bot: bool = False,
) -> None:
    if ban_as_bot:
        insult = get_witty_insult()
        await ctx.channel.send(
            f"I have chosen to ban <@{target}> for {timer}\n"
            f"May God have mercy on your soul, {insult}."
        )
    else:
        await ctx.channel.send(
            f"<@{ctx.discord_id}> has banned <@{target}> for {timer}\n"
            "May God have mercy on your soul."
        )
    current_ban = ctx.server_ctx.bans.get(target.id, -1)
    ctx.server_ctx.bans[target.id] = max(current_ban, time.time() + timer.seconds)

    # We need to save our state before sleeping so other workers will know
    # about this ban
    # TODO: What if *any* property update went to disk? Interesting idea...
    ctx.server_ctx.save()

    # Tell them they're unbanned 1 second late to ensure any weird delays
    # will still make the logic sound
    await asyncio.sleep(timer.seconds + 1)
    logging.info(f"Check if {target.id} is still banned")
    # TODO - This won't work since we're putting a lock around our object now
    # -- since we're saving/loading file every time, this will not check the
    # latest update. We need some concept of reload

    ctx.server_ctx.reload()

    # NOTE: We actually check that their ban should expire in the next few
    # seconds... otherwise it's possible while we were waiting that the user
    # got banned for *even longer* and we didn't know about it.
    # Logic here is that "ban ends within 30 seconds of now"
    bantime = ctx.server_ctx.bans[target.id]
    if bantime < time.time() and bantime != -1:
        insult = get_witty_insult()
        await ctx.channel.send(
            f"<@{target.id}>: you have been unbanned.\n"
            f"I hope you learned your lesson, *{insult}*."
        )


async def unban(
    ctx: MessageContext, target: DiscordUser
) -> None:
    ctx.server_ctx.bans[target.id] = -1
    await ctx.channel.send(
        f"<@{target.id}> has been unbanned early.\n"
        "You should think your benevolent savior.\n"
    )


async def macro_add(
    ctx: MessageContext, name: str, value: GreedyStr
) -> None:
    if name in ctx.server_ctx.macros:
        old = ctx.server_ctx.macros[name]
        await ctx.channel.send(
            f"Warning: <@{ctx.discord_id}> overwrote the macro for {name}\n"
            f"\t- Old macro: {old}\n\t+ New macro: {value}"
        )
    ctx.server_ctx.macros[name] = value
    await ctx.channel.send(f"Set macro for {name}")


async def macro_del(ctx: MessageContext, name: str) -> None:
    if name in ctx.server_ctx.macros:
        old = ctx.server_ctx.macros[name]
        await ctx.channel.send(
            f"Warning: <@{ctx.discord_id}> deleting the macro for {name}\n"
            f"\t- Old macro: {old}"
        )
        del ctx.server_ctx.macros[name]
        await ctx.channel.send(f"Deleted macro for {name}")
    else:
        insult = get_witty_insult()
        await ctx.channel.send(f"There's no macro defined for {name}, {insult}.")


async def m(ctx: MessageContext, name: str) -> None:
    if name in ctx.server_ctx.macros:
        await ctx.channel.send(ctx.server_ctx.macros[name])
    else:
        insult = get_witty_insult()
        await ctx.channel.send(f"There's no macro defined for {name}, {insult}.")
