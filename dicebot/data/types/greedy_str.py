#!/usr/bin/env python3

import shlex
from typing import List


class GreedyStr(str):
    """
    Special type designation for a string which should consume the rest
    of the arguments when parsing a command. Uses type hinting for some
    weird reflection stuff that kind of feels hacky and sketchy.
    """

    def __init__(self, s: str) -> None:
        self.s = s

    def unwrap(self) -> str:
        return self.s

    def unwrap_as_args(self) -> List[str]:
        splitter = shlex.shlex(self.s, posix=True)
        splitter.whitespace += ","
        splitter.whitespace_split = True
        return list(splitter)
