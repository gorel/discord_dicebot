#!/usr/bin/env python3

import command
from message_context import MessageContext
from models import GreedyStr


async def macro_add(ctx: MessageContext, name: str, value: GreedyStr) -> None:
    """Add a new macro to the server"""
    if name in ctx.server_ctx.macros:
        old = ctx.server_ctx.macros[name]
        await ctx.channel.send(
            f"Warning: <@{ctx.discord_id}> overwrote the macro for {name}\n"
            f"\t- Old macro: {old}\n\t+ New macro: {value}"
        )
    ctx.server_ctx.set_macro(name, value)
    await ctx.channel.send(f"Set macro for {name}")


async def macro_del(ctx: MessageContext, name: str) -> None:
    """Delete a macro from the server"""
    if name in ctx.server_ctx.macros:
        old = ctx.server_ctx.macros[name]
        await ctx.channel.send(
            f"Warning: <@{ctx.discord_id}> deleted the macro for {name}\n"
            f"\t- Old macro: {old}"
        )
        ctx.server_ctx.unset_macro(name)
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(f"There's no macro defined for {name}, {insult}.")


async def m(ctx: MessageContext, name: str) -> None:
    """Retrieve the value for a saved macro in this server"""
    if name in ctx.server_ctx.macros:
        await ctx.channel.send(ctx.server_ctx.macros[name])
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(f"There's no macro defined for {name}, {insult}.")
