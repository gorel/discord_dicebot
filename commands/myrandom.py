#!/urs/bin/env python3

import logging
import random

from message_context import MessageContext
from models import GreedyStr

async def choice(ctx: MessageContext, items: GreedyStr) -> None:
    """Get a random choice from a list of items"""
    choices = items.split(" ")
    logging.info(f"Choices are {choices}")
    response = random.choice(choices)
    await ctx.channel.send(response, reference=ctx.message)
