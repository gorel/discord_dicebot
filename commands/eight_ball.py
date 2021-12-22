#!/urs/bin/env python3

import logging
import random

from message_context import MessageContext
from models import GreedyStr

EIGHT_BALL_RESPONSES = [
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
]

async def eight_ball(ctx: MessageContext, _: GreedyStr) -> None:
    """Ask a question to the magic eight ball"""
    response = random.choice(EIGHT_BALL_RESPONSES)
    await ctx.channel.send(response, reference=ctx.message)
