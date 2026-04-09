#!/usr/bin/env python3

import datetime
import json
import logging

import pytz

from dicebot.commands.ask import AskOpenAI
from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.tasks.remind import send_reminder

log = logging.getLogger(__name__)

_PARSE_PROMPT = """\
Current date and time: {datetime_str} ({timezone})
User input: "{user_text}"

Extract the reminder time and the thing to be reminded about.
Respond with JSON only, no other text:
{{
  "seconds_until": <integer seconds from now, or -1 if no time is specified>,
  "reminder_text": "<what the user wants to be reminded about, as a clean short phrase>",
  "time_description": "<human-readable time, e.g. \\"in 5 minutes\\" or \\"at 12:00pm Thursday\\">"
}}"""

_ERROR_MSG = (
    "Sorry, I couldn't figure out when to remind you. "
    "Try something like 'in 5 minutes' or 'Thursday at noon'."
)

_MAX_SECONDS = 365 * 24 * 60 * 60  # 1 year


async def _parse_reminder(
    text: str, ctx: MessageContext
) -> tuple[int, str, str] | None:
    """Returns (seconds_until, reminder_text, time_description) or None if time cannot be parsed or is out of range."""
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
        reminder_text = str(data["reminder_text"])
        time_description = str(data["time_description"])
    except Exception:
        log.warning(f"Failed to parse AI response: {response!r}")
        return None

    if seconds_until < 0:
        return None

    if seconds_until > _MAX_SECONDS:
        return None

    return seconds_until, reminder_text, time_description


@register_command
async def remindme(ctx: MessageContext, text: GreedyStr) -> None:
    """Set a reminder for yourself"""
    result = await _parse_reminder(text.unwrap(), ctx)
    if result is None:
        await ctx.send(_ERROR_MSG)
        return
    seconds_until, reminder_text, time_description = result
    await ctx.send(f"Okay, <@{ctx.author_id}>, I'll remind you {time_description}")
    send_reminder.apply_async(
        (ctx.channel.id, ctx.author_id, reminder_text), countdown=seconds_until
    )
