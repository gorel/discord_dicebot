#!/usr/bin/env python3

import asyncio
import datetime
import logging
import random
import time

import db_helper
from commands import ban, roll_remind, timezone
from message_context import MessageContext
from models import DiscordUser, GreedyStr, Time

MAX_NUM_ROLLS = 10


async def roll(ctx: MessageContext, num_rolls_str: GreedyStr) -> None:
    """Roll a die for the server based on the current roll"""
    guild_id = ctx.server_ctx.guild_id
    next_roll = ctx.server_ctx.current_roll
    username = ctx.message.author.name

    last_roll_time = db_helper.get_last_roll_time(ctx.db_conn, guild_id, ctx.discord_id)
    now = datetime.datetime.now()

    if last_roll_time is not None:
        last_roll_unixtime = int(time.mktime(last_roll_time.timetuple()))
        last_roll_str = timezone.localize(last_roll_unixtime, ctx.server_ctx.tz)
        logging.info(f"{ctx.discord_id} last rolled {last_roll_str}")

        last_roll_delta = int((now - last_roll_time).total_seconds() // 3600)
        timeout = ctx.server_ctx.roll_timeout_hours
        if last_roll_delta < timeout:
            await ctx.channel.send(
                f"<@{ctx.discord_id}> last rolled {last_roll_str}.\n"
                f"This server only allows rolling once every {timeout} hours.\n"
            )
            ban_time = Time("1hr")
            await ban.ban(ctx, DiscordUser(ctx.discord_id), ban_time, ban_as_bot=True)
            # Bail early - don't allow rolling
            return

    logging.info(f"Next roll in server({guild_id}) for {username} is {next_roll}")

    try:
        logging.info(f"num rolls: {num_rolls_str}")
        rolls_remaining = int(float(num_rolls_str))
    except ValueError:
        rolls_remaining = 1

    gambling_penalty = max(rolls_remaining - 1, 0)

    if rolls_remaining <= 0:
        await ctx.channel.send("How... dumb are you?")
        ban_time = Time(f"{next_roll + gambling_penalty}hr")
        await ban.ban(ctx, DiscordUser(ctx.discord_id), ban_time, ban_as_bot=True)
        return

    if rolls_remaining > next_roll > 1:
        await ctx.channel.send(
            "The National Problem Gambling Helpline (1-800-522-4700) is available 24/7 and is 100% confidential. This hotline connects callers to local health and government organizations that can assist with their gambling addiction."
        )
        return

    if rolls_remaining > MAX_NUM_ROLLS:
        await ctx.channel.send(
            f"You all keep spamming this, so I'm setting the max to {MAX_NUM_ROLLS}\n"
            "This is why we can't have nice things."
        )
        rolls_remaining = MAX_NUM_ROLLS

    no_match = True
    while rolls_remaining and no_match:
        logging.info(f"rolls_remaining: {rolls_remaining}, no_match: {no_match}")
        # optimistically hope for a good roll
        no_match = False
        rolls_remaining -= 1

        # Finally, actually roll the die
        roll = random.randint(1, next_roll)
        db_helper.record_roll(
            ctx.db_conn, guild_id, ctx.message.author.id, roll, next_roll
        )
        # TODO: Batch all these messages so the bot doesn't get rate limited
        await ctx.channel.send(f"```# {roll}\nDetails: [d{next_roll} ({roll})]```")
        logging.info(f"{username} rolled a {roll} (d{next_roll})")

        if roll == 1:
            await ctx.channel.send("Lol, you suck")
            ban_time = Time(f"{next_roll + gambling_penalty}hr")
            await ban.ban(ctx, DiscordUser(ctx.discord_id), ban_time, ban_as_bot=True)
        elif roll == next_roll - 1:
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
                await ctx.channel.send(
                    f"<@{ctx.discord_id}>: gets to rename the server!"
                )
        else:
            no_match = True

    if no_match and gambling_penalty:
        await ban.turboban(
            ctx,
            reference_msg=ctx.message,
            target=DiscordUser(ctx.discord_id),
            # max penalty of 1 week
            num_hours=min(gambling_penalty**2, 168),
        )

    # If the user has roll reminders set up, await that now
    # I'm not sure why, but we need to reload here
    ctx.server_ctx.reload()
    roll_timeout = ctx.server_ctx.roll_timeout_hours
    user_id = ctx.discord_id
    if roll_timeout > 0 and ctx.server_ctx.should_remind(user_id):
        logging.info(f"Sleeping {roll_timeout} hours then reminding {user_id} to roll")
        await asyncio.sleep(roll_timeout * 3600)
        await roll_remind.send_roll_reminder(ctx, ctx.message.author)
