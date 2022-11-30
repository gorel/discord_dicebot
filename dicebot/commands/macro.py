#!/usr/bin/env python3

import dicebot.simple_utils
from dicebot.data.message_context import MessageContext
from dicebot.data.types.greedy_str import GreedyStr


async def macro_add(ctx: MessageContext, name: str, value: GreedyStr) -> None:
    """Add a new macro to the server"""
    macro = await ctx.guild.get_macro(ctx.session, name)
    if macro is not None and macro.author != ctx.author:
        await ctx.channel.send(
            "Macro already exists for {name}.\n"
            "Delete it first if you want to record a new macro."
        )
    await ctx.guild.add_macro(ctx.session, name, value, ctx.author)
    await ctx.session.commit()
    await ctx.channel.send(f"Set macro for {name}")


async def macro_del(ctx: MessageContext, name: str) -> None:
    """Delete a macro from the server"""
    macro = await ctx.guild.get_macro(ctx.session, name)
    if macro is not None:
        await ctx.session.delete(macro)
        await ctx.session.commit()
        await ctx.channel.send(
            f"Warning: <@{ctx.author_id}> deleted the macro for {name}\n"
        )
    else:
        insult = dicebot.simple_utils.get_witty_insult()
        await ctx.channel.send(f"There's no macro defined for {name}, {insult}.")


async def m(ctx: MessageContext, name: str) -> None:
    """Retrieve the value for a saved macro in this server"""
    macro = await ctx.guild.get_macro(ctx.session, name)
    if macro is not None:
        await ctx.channel.send(macro.value)
    else:
        insult = dicebot.simple_utils.get_witty_insult()
        await ctx.channel.send(f"There's no macro defined for {name}, {insult}.")
