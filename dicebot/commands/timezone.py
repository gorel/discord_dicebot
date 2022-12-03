#!/usr/bin/env python3

import datetime
import time

import pytz

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


def _localize_pretty(
    now_localized: datetime.datetime,
    target_localized: datetime.datetime,
) -> str:
    delta = target_localized - now_localized
    td0 = datetime.timedelta(0)
    in_past = delta < td0
    delta = abs(delta)

    if delta < datetime.timedelta(minutes=1):
        # Less than a minute
        specifier = "ago" if in_past else "from now"
        seconds = int(delta.total_seconds())
        plural = "s" if seconds > 1 else ""
        return f"{seconds} second{plural} {specifier}"
    elif delta < datetime.timedelta(hours=1):
        # Longer than a minute, less than an hour
        specifier = "ago" if in_past else "from now"
        minutes = int(delta.total_seconds()) // 60
        plural = "s" if minutes > 1 else ""
        return f"{minutes} minute{plural} {specifier}"
    elif (
        target_localized.day == now_localized.day + 1
        or target_localized.day == now_localized.day - 1
    ):
        # Happening in a different day (and longer than an hour)
        # The "longer than an hour" matters because if we're converting a target
        # datetime at 11:50pm, "2 hours from now" is completely valid for 2am.
        specifier = "yesterday" if in_past else "tomorrow"
        return target_localized.strftime(f"{specifier} at %I:%M %p %Z")
    elif delta < datetime.timedelta(days=1):
        # Longer than an hour, less than a day
        specifier = "ago" if in_past else "from now"
        hours, seconds = divmod(int(delta.total_seconds()), 3600)
        minutes = seconds // 60
        plural_hr = "s" if hours > 1 else ""
        plural_min = "s" if minutes > 1 else ""
        if minutes > 0:
            return f"{hours} hour{plural_hr}, {minutes} minute{plural_min} {specifier}"
        else:
            return f"{hours} hour{plural_hr} {specifier}"
    elif delta < datetime.timedelta(days=7):
        # Longer than a day, but less than a week
        if in_past:
            return target_localized.strftime("last %A at %I:%M %p %Z")
        else:
            return target_localized.strftime("%A at %I:%M %p %Z")
    elif now_localized.year != target_localized.year:
        # Happening in a different year (and longer than a week)
        # The "longer than a week" matters because if we're converting a target
        # datetime on Dec 31, "tomorrow" is completely valid for a Jan 1 date.
        return target_localized.strftime("%b %d, %Y at %I:%M %p %Z")
    else:
        # Longer than a week, but still happening this year
        return target_localized.strftime("%b %d at %I:%M %p %Z")


def localize(unixtime: int, tz: str) -> str:
    target_dt = datetime.datetime.utcfromtimestamp(unixtime)
    target_utc = pytz.utc.localize(target_dt)

    now_dt = datetime.datetime.utcfromtimestamp(int(time.time()))
    now_utc = pytz.utc.localize(now_dt)

    new_tz = pytz.timezone(tz)

    target_localized = target_utc.astimezone(new_tz)
    now_localized = now_utc.astimezone(new_tz)
    return _localize_pretty(now_localized, target_localized)


@requires_admin
@register_command
async def set_tz(ctx: MessageContext, tz: str) -> None:
    try:
        # Just ensure that pytz recognizes this as a valid timezone
        pytz.timezone(tz)
        ctx.guild.timezone = tz
        await ctx.session.commit()
        await ctx.channel.send(f"Set this server's timezone to '{tz}'")
    except pytz.UnknownTimeZoneError:
        await ctx.channel.send(f"Unknown timezone '{tz}'")
