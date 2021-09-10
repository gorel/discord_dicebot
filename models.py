#!/usr/bin/env python3

import enum
from typing import Generic, TypeVar


T = TypeVar("T")


class GreedyStr(str):
    """
    Special type designation for a string which should consume the rest
    of the arguments when parsing a command. Uses type hinting for some
    weird reflection stuff that kind of feels hacky and sketchy.
    """


class BotParam(Generic[T]):
    """
    Special type designation for a type which should be kept *secret* from
    usage helptext. This is useful for bot-only arguments such as changing
    the actor to be the bot itself instead of the original message sender.
    """


class SetMessageSubcommand(enum.Enum):
    WIN = 1
    LOSE = 2

    @classmethod
    def from_str(cls, s: str) -> "SetMessageSubcommand":
        if s.strip().lower() == "win":
            return SetMessageSubcommand.WIN
        elif s.strip().lower() == "lose":
            return SetMessageSubcommand.LOSE
        else:
            raise ValueError(f"Could not parse {s} as SetMessageSubcommand")


class Rename(enum.Enum):
    SERVER = 1
    TEXT_CHAT = 2


class Time:
    def __init__(self, s: str) -> None:
        self.s = s

    def __str__(self) -> str:
        return f"{self.s} ({self.seconds} seconds)"

    def __repr__(self) -> str:
        return str(self)

    @property
    def seconds(self) -> int:
        units = {}
        units["s"] = 1
        units["m"] = units["s"] * 60
        units["h"] = units["m"] * 60
        units["d"] = units["h"] * 24
        units["y"] = units["d"] * 365

        seconds = 0
        idx = 0
        while idx < len(self.s):
            builder = 0
            # Get value
            while idx < len(self.s) and self.s[idx].isdigit():
                builder = builder * 10 + int(self.s[idx])
                idx += 1
            # Now get unit
            unit_value = units[self.s[idx]]
            # Consume until end of units or string
            while idx < len(self.s) and not self.s[idx].isdigit():
                idx += 1
            # Add to total
            seconds += builder * unit_value
        return seconds


class DiscordUser:
    def __init__(self, discord_id: int) -> None:
        self.id = discord_id

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_str(cls, s: str) -> "DiscordUser":
        if len(s) > 0 and s[0] == "<" and s[-1] == ">":
            s = s[1:-1]
        if len(s) > 0 and s[0:2] == "@!":
            s = s[2:]
        elif len(s) > 0 and s[0] == "@":
            # Sometimes there's a leading @ but no ! -- I don't know why
            s = s[1:]
        return DiscordUser(int(s))
