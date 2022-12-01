#!/urs/bin/env python3

import logging
import random

from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.greedy_str import GreedyStr


@register_command
async def choice(ctx: MessageContext, items: GreedyStr) -> None:
    """Get a random choice from a list of items"""
    items_str = items.unwrap()
    choices = items_str.split(" ")
    logging.info(f"Choices are {choices}")
    response = random.choice(choices)
    await ctx.channel.send(response, reference=ctx.message)
