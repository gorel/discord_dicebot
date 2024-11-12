#!/usr/bin/env python3
from __future__ import annotations

import datetime
import logging
import re

import dateutil.parser
import pytz

from dicebot.data.types.message_context import MessageContext

OLD_STYLE_REGEX = re.compile(r"\d+[smhdy]")


class Time:
    s: str

    def __init__(self, s: str) -> None:
        self.logger = logging.getLogger(__name__)
        self.s = s
        self.datetime = None
        self.seconds = self._old_style_seconds(s)
        self.str = f"in {self.s} ({self.seconds} seconds)"

    # Adapted from https://stackoverflow.com/a/13430049
    def _parse_future(self, s: str, tz: datetime.tzinfo | None) -> datetime.datetime:
        """Same as dateutil.parser.parse() but only returns future dates."""
        now = datetime.datetime.now(tz=tz)
        default = now.replace(hour=0, minute=0, second=0, microsecond=0)
        for _ in range(365):
            dt = dateutil.parser.parse(s, default=default)
            self.logger.info(f"Parsed {dt} (vs now, {now})")
            if dt > now:
                return dt
            default += datetime.timedelta(days=1)
            default = default.replace(hour=0, minute=0, second=0, microsecond=0)
        raise ValueError("Could not parse future date")

    def _old_style_seconds(self, s: str) -> int:
        units = {}
        units["s"] = 1
        units["m"] = units["s"] * 60
        units["h"] = units["m"] * 60
        units["d"] = units["h"] * 24
        units["y"] = units["d"] * 365

        seconds = 0
        idx = 0
        while idx < len(s):
            builder = 0
            # Get value
            while idx < len(s) and s[idx].isdigit():
                builder = builder * 10 + int(s[idx])
                idx += 1
            # Now get unit
            unit_value = units[s[idx]]
            # Consume until end of units or string
            while idx < len(s) and not s[idx].isdigit():
                idx += 1
            # Add to total
            seconds += builder * unit_value
        return seconds

    def __str__(self) -> str:
        return self.str

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_str_with_ctx(cls, s: str, ctx: MessageContext) -> Time:
        if OLD_STYLE_REGEX.match(s) is not None:
            return cls(s)

        res = cls("0s")

        if "@" in s:
            s = s.replace("@", " ")
        res.s = s
        try:
            res.logger.info(f"Trying to parse {s} as a datetime")
            timezone = None
            if ctx is not None:
                try:
                    res.logger.info(f"Trying to parse timezone: {ctx.guild.timezone}")
                    timezone = pytz.timezone(ctx.guild.timezone)
                    res.logger.info(f"Parsed guild timezone: {timezone}")
                except Exception:
                    pass
            now = datetime.datetime.now(tz=timezone)
            res.datetime = res._parse_future(s, timezone)
            res.seconds = int((res.datetime - now).total_seconds())
            if res.datetime - now < datetime.timedelta(days=1):
                # Just print like 10:00am
                res.str = res.datetime.strftime("at %-I:%M%P")
            else:
                # Full date string
                res.str = res.datetime.strftime("at %Y-%m-%d %-I:%M%P")
            res.logger.info(f"Parsed to {res.str} ({res.datetime})")
        except Exception:
            res.datetime = None
            res.seconds = res._old_style_seconds(s)
            res.str = f"in {res.s} ({res.seconds} seconds)"
            res.logger.info(f"Parsed to {res.str} -- could not parse as datetime")

        return res
