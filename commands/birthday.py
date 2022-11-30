#!/usr/bin/env python3

import dateutil.parser

from data_infra.greedy_str import GreedyStr
from data_infra.message_context import MessageContext


async def birthday(ctx: MessageContext, birthday: GreedyStr) -> None:
    """Remember a user's birthday so we can wish them a happy birthday later"""
    try:
        dateutil.parser.parse(birthday)
    except dateutil.parser.ParserError:
        await ctx.channel.send("I have no idea when that is. Try again.")
    else:
        ctx.author.birthday = birthday
        await ctx.session.commit()
        await ctx.channel.send("Okay, I'll remember your birthday for later!")
