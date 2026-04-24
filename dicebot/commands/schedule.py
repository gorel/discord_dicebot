#!/usr/bin/env python3

import datetime
import json
import logging

import discord
import pytz

from dicebot.commands import timezone
from dicebot.commands.admin import requires_admin
from dicebot.commands.ask import AskOpenAI
from dicebot.core.register_command import register_command
from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext

log = logging.getLogger(__name__)

_PARSE_PROMPT = """\
Current date and time: {datetime_str} ({timezone})
User input: "{user_text}"

Extract the event name and when it is scheduled.
Respond with JSON only, no other text:
{{
  "seconds_until": <integer seconds from now until the event, or -1 if no time is specified>,
  "event_name": "<the name of the event, e.g. 'Jackbox' or 'Movie Night'>",
  "time_description": "<human-readable time, e.g. \\"April 17 at 5pm PT\\">"
}}"""

_ERROR_MSG = (
    "Sorry, I couldn't figure out when to schedule that. "
    "Try something like '!schedule jackbox on april 17 at 5pm'."
)

_MAX_SECONDS = 365 * 24 * 60 * 60  # 1 year


async def _parse_schedule(text: str, ctx: MessageContext) -> tuple[int, str, str] | None:
    """Returns (seconds_until, event_name, time_description) or None on failure."""
    try:
        tz = pytz.timezone(ctx.guild.timezone)
        timezone_name = ctx.guild.timezone
    except pytz.exceptions.UnknownTimeZoneError:
        tz = pytz.utc
        timezone_name = "UTC"

    now = datetime.datetime.now(tz=tz)
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
    prompt = _PARSE_PROMPT.format(
        datetime_str=datetime_str,
        timezone=timezone_name,
        user_text=text,
    )

    response = await AskOpenAI().ask(prompt)
    try:
        data = json.loads(response)
        seconds_until = int(data["seconds_until"])
        event_name = str(data["event_name"])
        time_description = str(data["time_description"])
    except Exception:
        log.warning(f"Failed to parse AI schedule response: {response!r}")
        return None

    if seconds_until <= 0 or seconds_until > _MAX_SECONDS:
        return None

    return seconds_until, event_name, time_description


@register_command
async def schedule(ctx: MessageContext, text: GreedyStr) -> None:
    """Schedule a game night event. React with 👀 to get notified!"""
    async with ctx.channel.typing():
        result = await _parse_schedule(text.unwrap(), ctx)
        if result is None:
            await ctx.send(_ERROR_MSG)
            return

        seconds_until, event_name, time_description = result

        # Compute event_time as UTC datetime (naive, stored without tzinfo)
        event_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(seconds=seconds_until)

        # Create the event record (message_id filled in after we post)
        event = ScheduledEvent(
            guild_id=ctx.guild_id,
            channel_id=ctx.channel.id,
            name=event_name,
            event_time=event_time,
        )
        ctx.session.add(event)
        await ctx.session.commit()
        await ctx.session.refresh(event)

        # Post the signup message
        signup_msg = await ctx.channel.send(
            f"**{event_name}** is scheduled for {time_description}. React with 👀 to get notified!"
        )

        # Store message_id on the event
        event.message_id = signup_msg.id
        await ctx.session.commit()

        # Dispatch the notification task (lazy import to avoid circular imports)
        from dicebot.tasks.notify_event import notify_event
        notify_event.apply_async(
            (event.id, ctx.channel.id),
            countdown=seconds_until,
        )


@requires_admin
@register_command
async def cancel_event(ctx: MessageContext, event_id: int) -> None:
    """Cancel a scheduled event by ID (admin only)"""
    event = await ScheduledEvent.get_by_id(ctx.session, event_id)
    if event is None:
        await ctx.send(f"No event found with ID {event_id}.")
        return

    # Delete signups first, then event
    signups = await ScheduledEventSignup.get_all_for_event(ctx.session, event.id)
    for signup in signups:
        await ctx.session.delete(signup)
    await ctx.session.delete(event)
    await ctx.session.commit()
    await ctx.send(f"Event **{event.name}** (ID: {event_id}) has been cancelled.")


@register_command
async def list_events(ctx: MessageContext) -> None:
    """List upcoming scheduled events for this server."""
    events = await ScheduledEvent.get_upcoming(ctx.session, ctx.guild_id)
    embed = discord.Embed(title="Upcoming Events", color=discord.Color.blue())
    if not events:
        embed.add_field(name="​", value="No upcoming events scheduled.", inline=False)
    else:
        for event in events:
            time_str = timezone.localize_dt(event.event_time, ctx.guild.timezone)
            embed.add_field(name=event.name, value=time_str, inline=False)
    await ctx.send(embed=embed)
