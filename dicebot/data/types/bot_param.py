#!/usr/bin/env python3

from typing import Generic, TypeVar

T = TypeVar("T")


class BotParam(Generic[T]):
    """
    Special type designation for a type which should be kept *secret* from
    usage helptext. This is useful for bot-only arguments such as changing
    the actor to be the bot itself instead of the original message sender.
    """
