#!/usr/bin/env python3

from __future__ import annotations

import types
from typing import Protocol, Union, get_args, get_origin, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.types.message_context import MessageContext


@runtime_checkable
class _FromStrProtocol(Protocol):
    @classmethod
    def from_str(cls, s: str) -> _FromStrProtocol:
        """Class method that constructs itself from a string"""
        # Appease the type checker
        return cls.from_str(s)


@runtime_checkable
class _FromStrWithCtxProtocol(Protocol):
    @classmethod
    def from_str_with_ctx(cls, s: str, ctx: MessageContext) -> _FromStrProtocol:
        """Class method that constructs itself from a string"""
        # Appease the type checker
        return cls.from_str_with_ctx(s, ctx)


@runtime_checkable
class _StrCallProtocol(Protocol):
    def __init__(self, s: str) -> None:
        """Class that accepts a string single-argument constructor."""

    @classmethod
    def __call__(cls, s: str) -> _StrCallProtocol:
        """Class that accepts a string single-argument constructor.
        Duplicating this as __call__ helps the type checker."""
        return cls(s)


@runtime_checkable
class _LoadFromCmdStrProtocol(Protocol):
    @classmethod
    async def load_from_cmd_str(
        cls, session: AsyncSession, s: str
    ) -> _LoadFromCmdStrProtocol:
        """Class method that constructs itself from a string"""
        return await cls.load_from_cmd_str(session, s)


StrTypifiable = (
    _FromStrProtocol
    | _FromStrWithCtxProtocol
    | _StrCallProtocol
    | _LoadFromCmdStrProtocol
)


def _unwrap_optional(typ):
    """If typ is Optional[T] (i.e. Union[T, None]), return T. Otherwise return typ as-is."""
    if get_origin(typ) is Union:
        args = [a for a in get_args(typ) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return typ


async def typify_str(
    ctx: MessageContext, typ: StrTypifiable, value: str
) -> StrTypifiable:
    typ = _unwrap_optional(typ)
    if isinstance(typ, _FromStrWithCtxProtocol):
        return typ.from_str_with_ctx(value, ctx=ctx)
    if isinstance(typ, _FromStrProtocol):
        # assert getattr(typ, "from_str", None) is not None
        return typ.from_str(value)
    elif isinstance(typ, _LoadFromCmdStrProtocol):
        return await typ.load_from_cmd_str(ctx.session, value)
    elif isinstance(typ, _StrCallProtocol):
        return typ(value)
