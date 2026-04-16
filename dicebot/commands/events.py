#!/usr/bin/env python3

from dicebot.commands import timezone
from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.db.active_event import ActiveEvent
from dicebot.data.types.message_context import MessageContext


@requires_admin
@register_command
async def events_on(ctx: MessageContext, probability: float) -> None:
    """Enable random events for this server with the given probability (0.0-1.0)"""
    if not (0 < probability <= 1.0):
        await ctx.send(
            "Probability must be between 0 (exclusive) and 1.0 (inclusive)."
        )
        return
    ctx.guild.events_probability = probability
    ctx.guild.events_channel_id = ctx.channel.id
    await ctx.session.commit()
    await ctx.send(
        f"Random events enabled with {probability:.0%} daily chance. "
        "Events will be announced in this channel."
    )


@requires_admin
@register_command
async def events_off(ctx: MessageContext) -> None:
    """Disable random events for this server"""
    ctx.guild.events_probability = None
    ctx.guild.events_channel_id = None
    await ctx.session.commit()
    await ctx.send("Random events disabled.")


@register_command
async def events_status(ctx: MessageContext) -> None:
    """Check the current random events status for this server"""
    if ctx.guild.events_probability is None:
        await ctx.send("Random events are disabled for this server.")
        return

    active = await ActiveEvent.get_current(ctx.session, ctx.guild_id)
    if active:
        event_name = active.event_type_enum.value.replace("_", " ").title()
        expires = timezone.localize_dt(active.expires_at, ctx.guild.timezone)
        await ctx.send(
            f"Random events are enabled ({ctx.guild.events_probability:.0%} daily chance).\n"
            f"Today's event: **{event_name}**\n"
            f"Expires: {expires}"
        )
    else:
        await ctx.send(
            f"Random events are enabled ({ctx.guild.events_probability:.0%} daily chance).\n"
            "No event active today."
        )
