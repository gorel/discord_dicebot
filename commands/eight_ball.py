#!/urs/bin/env python3

import asyncio
import logging
import random

from commands import ban
from message_context import MessageContext
from models import DiscordUser, GreedyStr

RANDOM_BAN_THRESHOLD = 0.05
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
    if random.random() < RANDOM_BAN_THRESHOLD:
        await ctx.channel.send(
            "This is such a stupid question, I'm just going to ban you instead of answering it.",
            reference=ctx.message,
        )
        await asyncio.sleep(3)
        await ban.ban(
            ctx,
            target=DiscordUser(ctx.message.author.id),
            timer=Time("1hr"),
            ban_as_bot=True,
        )
    else:
        response = random.choice(EIGHT_BALL_RESPONSES)
        await ctx.channel.send(response, reference=ctx.message)
