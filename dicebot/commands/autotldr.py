#!/usr/bin/env python3

from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@register_command
async def autotldr(ctx: MessageContext) -> None:
    """Flip the server's autotldr setting"""
    ctx.guild.auto_tldr = not ctx.guild.auto_tldr
    await ctx.quote_reply(f"Set autotldr to {ctx.guild.auto_tldr}")
