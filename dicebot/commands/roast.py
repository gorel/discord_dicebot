#!/usr/bin/env python3

import logging

from dicebot.commands.ask import AskOpenAI
from dicebot.data.types.message_context import MessageContext


async def generate_roast(ctx: MessageContext, roll: int, die_size: int) -> None:
    """Generate and send an AI roast for a critical fail roll."""
    try:
        name = ctx.message.author.name
        prompt = (
            f"Write a short, savage roast (2-3 sentences) for someone named {name} "
            f"who just rolled a {roll} on a d{die_size} in a Discord dice game. "
            "Be creative and mean-spirited but keep it PG-13."
        )
        response = await AskOpenAI().ask(prompt, channel=ctx.channel)
        await ctx.send(response)
    except Exception as e:
        logging.warning(f"Failed to generate roast: {e}")
