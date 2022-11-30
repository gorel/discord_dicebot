#!/usr/bin/env python3

import dicebot.simple_utils
from dicebot.data.message_context import MessageContext
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.set_message_subcommand import SetMessageSubcommand


async def set_msg(
    ctx: MessageContext,
    win_or_lose: SetMessageSubcommand,
    msg: GreedyStr,
) -> None:
    """Set the win/loss message in this server for critical success or failure"""
    msg_str = msg.unwrap()
    if dicebot.simple_utils.is_admin(ctx.message.author):
        if win_or_lose is SetMessageSubcommand.WIN:
            ctx.guild.critical_success_msg = msg_str
            await ctx.session.commit()
            await ctx.channel.send(f"Set the win message to '{msg_str}'")
        else:
            ctx.guild.critical_failure_msg = msg_str
            await ctx.session.commit()
            await ctx.channel.send(f"Set the lose message to '{msg_str}'")
    else:
        await ctx.channel.send(f"You're not an admin.\nThis incident will be recorded.")
