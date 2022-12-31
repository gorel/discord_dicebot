#!/usr/bin/env python3

import re
from typing import List

from dicebot.core.register_command import register_command
from dicebot.data.db.thanks import Thanks
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext

SHORT_REASON_THRESHOLD = 20
AT_MENTION_REGEX = re.compile(r"<@!?(.*?)>")


async def extract_targets(msg: str) -> List[int]:
    res = []
    match = AT_MENTION_REGEX.findall(msg)
    for discord_id in match:
        res.append(int(discord_id))
    return res


@register_command
async def thanks(
    ctx: MessageContext,
    reason: GreedyStr,
) -> None:
    """Thank a set of users for doing something nice.
    You should @mention everyone you want to thank."""

    reason_str = reason.unwrap()
    targets = await extract_targets(ctx.message.content)
    if len(targets) == 0:
        await ctx.channel.send(
            "Hmm, I couldn't find any @mention in your message.\n"
            "Try sending your message again but remember to tag at least one person."
        )
        return

    thanks = []
    for target in targets:
        thanks.append(
            Thanks(
                guild_id=ctx.guild_id,
                thanker_id=ctx.message.author.id,
                thankee_id=target,
                reason=reason_str,
            )
        )
    ctx.session.add_all(thanks)
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
