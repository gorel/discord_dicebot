#!/usr/bin/env python3

from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


@register_command
async def macro_add(ctx: MessageContext, name: str, value: GreedyStr) -> None:
    """Add a new macro to the server"""
    value_str = value.unwrap()
    macro = await ctx.guild.get_macro(ctx.session, name)
    if macro is not None:
        await ctx.channel.send(
            "Macro already exists for {name}.\n"
            "Delete it first if you want to record a new macro."
        )
    else:
        await ctx.guild.add_macro(ctx.session, name, value_str, ctx.author)
        await ctx.session.commit()
        await ctx.channel.send(f"Set macro for {name}")


@register_command
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
        await ctx.channel.send(f"There's no macro defined for {name}.")


@register_command
async def m(ctx: MessageContext, name: str) -> None:
    """Retrieve the value for a saved macro in this server"""
    macro = await ctx.guild.get_macro(ctx.session, name)
    if macro is not None:
        await ctx.channel.send(macro.value)
    else:
        await ctx.channel.send(f"There's no macro defined for {name}.")
