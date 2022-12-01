#!/usr/bin/env python3

import functools

# This will get populated with the register_command
# decorator below
REGISTERED_COMMANDS = []


def register_command(coro):
    """Mark a command as a registered command for use in this bot.
    This is used as a decorator for applicable functions"""
    # TODO: Verify coro has the proper typification (maybe with Protocol)
    REGISTERED_COMMANDS.append(coro)

    @functools.wraps(coro)
    async def wrapper(*args, **kwargs):
        return await coro(*args, **kwargs)

    return wrapper
