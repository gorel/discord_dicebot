#!/usr/bin/env python3


class GreedyStr(str):
    """
    Special type designation for a string which should consume the rest
    of the arguments when parsing a command. Uses type hinting for some
    weird reflection stuff that kind of feels hacky and sketchy.
    """
