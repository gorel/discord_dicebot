#!/usr/bin/env python3

from __future__ import annotations

from typing import Protocol, runtime_checkable

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
class _StrCallProtocol(Protocol):
    def __init__(self, s: str) -> None:
        """Class that accepts a string single-argument constructor."""

    @classmethod
    def __call__(cls, s: str) -> _StrCallProtocol:
        """Class that accepts a string single-argument constructor.
        Duplicating this as __call__ helps the type checker."""
        return cls(s)


@runtime_checkable
class _StrCallWithCtxProtocol(Protocol):
    def __init__(self, s: str, ctx: MessageContext | None = None) -> None:
        """Class that accepts a string and ctx constructor."""

    @classmethod
    def __call__(
        cls, s: str, ctx: MessageContext | None = None
    ) -> _StrCallWithCtxProtocol:
        """Class that accepts a string and ctx constructor.
        Duplicating this as __call__ helps the type checker."""
        return cls(s, ctx)


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
    | _StrCallProtocol
    | _StrCallWithCtxProtocol
    | _LoadFromCmdStrProtocol
)


async def typify_str(
    ctx: MessageContext, typ: StrTypifiable, value: str
) -> StrTypifiable:
    if isinstance(typ, _StrCallWithCtxProtocol):
        return typ(value, ctx=ctx)
    if isinstance(typ, _FromStrProtocol):
        # assert getattr(typ, "from_str", None) is not None
        return typ.from_str(value)
    elif isinstance(typ, _LoadFromCmdStrProtocol):
        return await typ.load_from_cmd_str(ctx.session, value)
    elif isinstance(typ, _StrCallProtocol):
        return typ(value)
