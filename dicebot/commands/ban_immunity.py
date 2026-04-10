#!/usr/bin/env python3

from dicebot.commands import timezone
from dicebot.commands.admin import requires_admin
from dicebot.commands.ban import unban_internal
from dicebot.core.register_command import register_command
from dicebot.data.db.ban_immunity import BanImmunity
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time


@requires_admin
@register_command
async def grant_immunity(ctx: MessageContext, target: User, timer: Time) -> None:
    """Grant a user ban immunity for the specified duration"""
    immunity = await BanImmunity.grant(
        ctx.session,
        ctx.guild,
        target,
        ctx.author,
        timer.seconds,
    )
    localized = timezone.localize_dt(immunity.immune_until, ctx.guild.timezone)
    await ctx.send(
        f"{target.as_mention()} has been granted ban immunity until {localized}."
    )
    if await target.is_currently_banned(ctx.session, ctx.guild):
        await unban_internal(
            ctx, target, f"{target.as_mention()} has been unbanned due to ban immunity."
        )
