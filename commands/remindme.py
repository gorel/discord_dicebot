#!/usr/bin/env python3

import asyncio
import logging

from data_infra.greedy_str import GreedyStr
from data_infra.message_context import MessageContext
from data_infra.time import Time


async def remindme(ctx: MessageContext, timer: Time, text: GreedyStr) -> None:
    """Set a reminder for yourself"""
    # TODO: Allow specifying a certain date instead
    await ctx.channel.send(f"Okay, <@{ctx.discord_id}>, I'll remind you in {timer}")
    logging.info(f"Will now sleep for {timer.seconds} seconds for reminder")
    await asyncio.sleep(timer.seconds)
    await ctx.channel.send(f"Reminder for <@{ctx.discord_id}>: {text}")
