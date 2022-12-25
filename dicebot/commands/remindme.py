#!/usr/bin/env python3

from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time
from dicebot.tasks.remind import send_reminder


@register_command
async def remindme(ctx: MessageContext, timer: Time, text: GreedyStr) -> None:
    """Set a reminder for yourself"""
    text_str = text.unwrap()
    # TODO: Allow specifying a certain date instead
    await ctx.channel.send(f"Okay, <@{ctx.author_id}>, I'll remind you in {timer}")
    send_reminder.apply_async(
        (ctx.channel.id, ctx.author_id, text_str), countdown=timer.seconds
    )
