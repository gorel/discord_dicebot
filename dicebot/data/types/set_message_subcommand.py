#!/usr/bin/env python3

from __future__ import annotations

from enum import Enum, auto


class SetMessageSubcommand(Enum):
    WIN = auto()
    LOSE = auto()

    @classmethod
    def from_str(cls, s: str) -> SetMessageSubcommand:
        s_stripped = s.strip().lower()
        if s_stripped == "win":
            return SetMessageSubcommand.WIN
        elif s_stripped == "lose":
            return SetMessageSubcommand.LOSE
        else:
            raise ValueError(f"Could not parse {s} as SetMessageSubcommand")
