#!/usr/bin/env python3

from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext

@register_command
async def scags(ctx: MessageContext) -> None:
    """Ridicule the user for using the wrong command"""
    await ctx.quote_reply("You moron, the command you're looking for is `!m scags`")
