#!/usr/bin/env python3


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
