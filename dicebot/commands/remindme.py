#!/usr/bin/env python3

import asyncio
import logging

from dicebot.core.register_command import register_command
from dicebot.data.message_context import MessageContext
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.time import Time


@register_command
async def remindme(ctx: MessageContext, timer: Time, text: GreedyStr) -> None:
    """Set a reminder for yourself"""
    text_str = text.unwrap()
    # TODO: Allow specifying a certain date instead
    await ctx.channel.send(f"Okay, <@{ctx.author_id}>, I'll remind you in {timer}")
    logging.info(f"Will now sleep for {timer.seconds} seconds for reminder")
    # TODO: Put into a background queue
    await asyncio.sleep(timer.seconds)
    await ctx.channel.send(f"Reminder for <@{ctx.author_id}>: {text_str}")
