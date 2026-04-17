#!/usr/bin/env python3

from dicebot.core.register_command import register_command
from dicebot.data.db.rep import Rep
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext


REP_MAX = 10000


@register_command
async def rep(ctx: MessageContext, amount: int, target: User) -> None:
    """Give rep to another user. Use negative amounts to take away rep."""
    if target.id == ctx.author_id:
        await ctx.send("You can't rep yourself.")
        return

    if amount > REP_MAX or amount < -REP_MAX:
        await ctx.send(f"Rep amount must be between -{REP_MAX:,} and {REP_MAX:,}.")
        return

    await Rep.give(
        ctx.session,
        guild_id=ctx.guild_id,
        giver_id=ctx.author_id,
        receiver_id=target.id,
        amount=amount,
    )

    total = await Rep.get_total_received(ctx.session, ctx.guild_id, target.id)
    await ctx.send(
        f"You gave {amount:+d} rep to {target.as_mention()}. "
        f"Their total rep is now {total:+d}."
    )
