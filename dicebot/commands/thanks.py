#!/usr/bin/env python3

from dicebot.core.register_command import register_command
from dicebot.data.db.thanks import Thanks
from dicebot.data.db.user import User
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext

SHORT_REASON_THRESHOLD = 20


@register_command
async def thanks(
    ctx: MessageContext,
    target: User,
    reason: GreedyStr,
) -> None:
    """Thank a user for doing something nice"""
    reason_str = reason.unwrap()
    thanks = Thanks(
        guild_id=ctx.guild_id,
        thanker_id=ctx.message.author.id,
        thankee_id=target.id,
        reason=reason_str,
    )
    ctx.session.add(thanks)
    await ctx.session.commit()
    msg = "Woohoo! Your `!thanks` has been recorded."
    if len(reason_str) < SHORT_REASON_THRESHOLD:
        msg += "\nNext time try adding more context on why you're thanking this person."
    await ctx.channel.send(msg)


@register_command
async def thanks_scoreboard(ctx: MessageContext) -> None:
    """Display the scoreboard for !thanks"""
    msg = await ctx.guild.thanks_scoreboard_str(ctx.client, ctx.session)
    await ctx.channel.send(msg)
