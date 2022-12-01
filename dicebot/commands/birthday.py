#!/usr/bin/env python3

import dateutil.parser

from dicebot.core.register_command import register_command
from dicebot.data.message_context import MessageContext
from dicebot.data.types.greedy_str import GreedyStr


@register_command
async def birthday(ctx: MessageContext, birthday: GreedyStr) -> None:
    """Remember a user's birthday so we can wish them a happy birthday later"""
    try:
        parsed_birthday = dateutil.parser.parse(birthday.unwrap())
    except dateutil.parser.ParserError:
        await ctx.channel.send("I have no idea when that is. Try again.")
    else:
        ctx.author.birthday = parsed_birthday
        await ctx.session.commit()
        await ctx.channel.send("Okay, I'll remember your birthday for later!")
