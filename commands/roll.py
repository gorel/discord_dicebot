#!/usr/bin/env python3

import asyncio
import datetime
import logging
import random

import db_helper
from commands import ban, roll_remind
from message_context import MessageContext
from models import DiscordUser, Time


async def roll(ctx: MessageContext) -> None:
    """Roll a die for the server based on the current roll"""
    guild_id = ctx.server_ctx.guild_id
    next_roll = ctx.server_ctx.current_roll
    username = ctx.message.author.name

    last_roll_time = db_helper.get_last_roll_time(ctx.db_conn, guild_id, ctx.discord_id)
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
           await ban.ban(ctx, DiscordUser(ctx.discord_id), ban_time, ban_as_bot=True)
           # Bail early - don't allow rolling
           return

    logging.info(f"Next roll in server({guild_id}) for {username} is {next_roll}")

    # Finally, actually roll the die
    roll = random.randint(1, next_roll)
    db_helper.record_roll(ctx.db_conn, guild_id, ctx.message.author.id, roll, next_roll)
    await ctx.channel.send(f"```# {roll}\nDetails: [d{next_roll} ({roll})]```")
    logging.info(f"{username} rolled a {roll} (d{next_roll})")

    if roll == 1:
        s = ctx.server_ctx.critical_failure_msg
        if s != "":
            await ctx.channel.send(f"<@{ctx.discord_id}>: {s}")
        else:
            await ctx.channel.send(
                f"<@{ctx.discord_id}>: gets to rename the chat channel!"
            )
    elif roll == next_roll:
        # Increment the current roll
        ctx.server_ctx.current_roll = next_roll + 1
        logging.info(f"Next roll in server({guild_id}) is now {next_roll + 1}")

        s = ctx.server_ctx.critical_success_msg
        if s != "":
            await ctx.channel.send(f"<@{ctx.discord_id}>: {s}")
        else:
            await ctx.channel.send(f"<@{ctx.discord_id}>: gets to rename the server!")

    # If the user has roll reminders set up, await that now
    # I'm not sure why, but we need to reload in case the reminder was recently
    # set up
    ctx.server_ctx.reload()
    roll_timeout = ctx.server_ctx.roll_timeout_hours
    user_id = ctx.discord_id
    if roll_timeout > 0 and ctx.server_ctx.should_remind(user_id):
        logging.info(f"Sleeping {roll_timeout} hours then reminding {user_id} to roll")
        await asyncio.sleep(roll_timeout * 3600)
        await roll_remind.send_roll_reminder(ctx, ctx.message.author)
