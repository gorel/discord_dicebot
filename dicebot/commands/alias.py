#!/usr/bin/env python3

from dicebot.commands import ban
from dicebot.core.register_command import register_command, REGISTERED_COMMANDS
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time


@register_command
async def alias(ctx: MessageContext, name: str, value: str) -> None:
    """Add a new command alias to the server"""
    if name in REGISTERED_COMMANDS:
        await ctx.send(
            "You can't alias a command that already exists.\n"
            "This incident will be recorded."
        )
        await ban.ban_internal(
            ctx,
            target=ctx.author,
            timer=Time("1hr"),
            ban_as_bot=True,
            reason="Tried to overwrite a built-in command",
        )
        return

    alias = await ctx.guild.get_alias(ctx.session, name)
    if alias is not None:
        await ctx.send(
            "Alias already exists for {name}.\n"
            "Delete it first if you want to record a new alias."
        )
    else:
        await ctx.guild.add_alias(ctx.session, name, value, ctx.author)
        await ctx.session.commit()
        await ctx.send(f"Set alias for {name}")


@register_command
async def alias_del(ctx: MessageContext, name: str) -> None:
    """Delete a alias from the server"""
    alias = await ctx.guild.get_alias(ctx.session, name)
    if alias is not None:
        await ctx.session.delete(alias)
        await ctx.session.commit()
        await ctx.send(f"Warning: <@{ctx.author_id}> deleted the alias for {name}\n")
    else:
        await ctx.send(f"There's no alias defined for {name}.")
