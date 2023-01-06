#!/usr/bin/env python3

import datetime
import logging
import random

from dicebot.commands import ban, timezone
from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.db.roll import Roll
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time

SPECIAL_ROLL_NUMBER = 69


@register_command
async def roll(ctx: MessageContext, num_rolls: GreedyStr) -> None:
    """Roll a die for the server based on the current roll"""
    num_rolls_str = num_rolls.unwrap()
    next_roll = ctx.guild.current_roll
    name = ctx.message.author.name

    last_roll = await Roll.get_last_roll(ctx.session, ctx.guild, ctx.author)
    now = datetime.datetime.now()

    if last_roll is not None:
        last_roll_str = timezone.localize_dt(last_roll.rolled_at, ctx.guild.timezone)
        logging.info(f"{ctx.author_id} last rolled {last_roll_str}")

        last_roll_delta = int((now - last_roll.rolled_at).total_seconds() // 3600)
        timeout = ctx.guild.roll_timeout
        if last_roll_delta < timeout:
            await ctx.channel.send(
                f"{ctx.author.as_mention()} last rolled {last_roll_str}.\n"
                f"This server only allows rolling once every {timeout} hours.\n"
            )
            ban_time = Time("1hr")
            await ban.ban_internal(
                ctx,
                ctx.author,
                ban_time,
                ban_as_bot=True,
                reason="Rolled too often",
            )
            # Bail early - don't allow rolling
            return

    logging.info(f"Next roll in guild({ctx.guild_id}) for {name} is {next_roll}")

    try:
        logging.info(f"num rolls: {num_rolls_str}")
        rolls_remaining = int(float(num_rolls_str))
    except ValueError:
        rolls_remaining = 1

    if rolls_remaining <= 0:
        await ctx.channel.send("How... dumb are you?")
        ban_time = Time(f"{next_roll}hr")
        await ban.ban_internal(
            ctx,
            ctx.author,
            ban_time,
            ban_as_bot=True,
            reason="Tried to roll a negative",
        )
        return

    if rolls_remaining > next_roll > 1:
        await ctx.channel.send(
            "The National Problem Gambling Helpline (1-800-522-4700) "
            "is available 24/7 and is 100% confidential. "
            "This hotline connects callers to local health and government "
            "organizations that can assist with their gambling addiction."
        )
        return

    if (
        ctx.guild.gambling_limit is not None
        and rolls_remaining > ctx.guild.gambling_limit
    ):
        await ctx.channel.send(
            f"This server has set the roll gambling limit to {ctx.guild.gambling_limit}"
        )
        rolls_remaining = ctx.guild.gambling_limit

    sent_message = False
    no_match = True
    roll_results_strings = []
    gambling_penalty = max(rolls_remaining - 1, 0)

    while rolls_remaining and no_match:
        logging.info(f"rolls_remaining: {rolls_remaining}, no_match: {no_match}")
        # optimistically hope for a good roll
        no_match = False
        rolls_remaining -= 1

        # Finally, actually roll the die
        roll = random.randint(1, next_roll)
        roll_obj = Roll(
            guild_id=ctx.guild_id,
            discord_user_id=ctx.author_id,
            actual_roll=roll,
            target_roll=next_roll,
        )
        ctx.session.add(roll_obj)
        await ctx.session.commit()

        # We batch all the roll messages so the bot doesn't get rate limited
        roll_results_strings.append(f"```# {roll}\nDetails: [d{next_roll} ({roll})]```")
        if roll == SPECIAL_ROLL_NUMBER:
            roll_results_strings.append("Nice")
        logging.info(f"{name} rolled a {roll} (d{next_roll})")

        if roll == 1:
            batched_rolls_message = "\n".join(roll_results_strings)
            await ctx.channel.send(batched_rolls_message)
            sent_message = True
            await ctx.channel.send("Lol, you suck")
            ban_time = Time(f"{next_roll + gambling_penalty}hr")
            await ban.ban_internal(
                ctx,
                ctx.author,
                ban_time,
                ban_as_bot=True,
                reason="Rolled a 1",
            )
        elif roll == next_roll - 1:
            batched_rolls_message = "\n".join(roll_results_strings)
            await ctx.channel.send(batched_rolls_message)
            sent_message = True
            if ctx.guild.allow_renaming:
                await ctx.guild.add_chat_rename(ctx.session, ctx.author)
                await ctx.session.commit()
                await ctx.channel.send(
                    f"{ctx.author.as_mention()} gets to rename the chat channel!"
                )
            else:
                await ctx.channel.send(
                    f"{ctx.author.as_mention()}: {ctx.guild.critical_failure_msg}"
                )
        elif roll == next_roll:
            # Increment the current roll
            ctx.guild.current_roll = next_roll + 1
            await ctx.session.commit()
            logging.info(f"Next roll in guild({ctx.guild_id}) is now {next_roll + 1}")

            batched_rolls_message = "\n".join(roll_results_strings)
            await ctx.channel.send(batched_rolls_message)
            sent_message = True

            if ctx.guild.allow_renaming:
                await ctx.guild.add_guild_rename(ctx.session, ctx.author)
                await ctx.session.commit()
                await ctx.channel.send(
                    f"{ctx.author.as_mention()}: gets to rename the server!"
                )
            else:
                await ctx.channel.send(
                    f"{ctx.author.as_mention()}: {ctx.guild.critical_success_msg}"
                )
        else:
            no_match = True

    # We're done rolling, send the batched message if we never sent it
    if not sent_message:
        batched_rolls_message = "\n".join(roll_results_strings)
        await ctx.channel.send(batched_rolls_message)

    if no_match and gambling_penalty:
        await ban.turboban(
            ctx,
            target=ctx.author,
            # max penalty of 1 week
            num_hours=min(gambling_penalty**2, 168),
            reason="Gambled and lost",
        )


@requires_admin
@register_command
async def set_gambling_limit(ctx: MessageContext, value: int) -> None:
    """Set the roll gambling limit for this server. Use -1 to remove the limit."""
    if value == -1:
        ctx.guild.gambling_limit = None
    else:
        ctx.guild.gambling_limit = value
    await ctx.session.commit()
    await ctx.channel.send(f"The roll gambling limit for this server is now {value}")
