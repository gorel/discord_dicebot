#!/usr/bin/env python3

import command
from message_context import MessageContext
from models import GreedyStr, SetMessageSubcommand


async def set_msg(
    ctx: MessageContext,
    win_or_lose: SetMessageSubcommand,
    msg: GreedyStr,
) -> None:
    """Set the win/loss message in this server for critical success or failure"""
    if command.has_diceboss_role(ctx.message.author):
        if win_or_lose is SetMessageSubcommand.WIN:
            ctx.server_ctx.critical_success_msg = msg
            await ctx.channel.send(f"Set the win message to '{msg}'")
        else:
            ctx.server_ctx.critical_failure_msg = msg
            await ctx.channel.send(f"Set the lose message to '{msg}'")
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(
           f"You're not a diceboss.\nDon't try that shit again, {insult}.")


