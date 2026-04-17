#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated, Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]


class Rep(Base):
    __tablename__ = "rep"

    id: Mapped[bigint_pk]
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    giver_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    receiver_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    amount: Mapped[int] = mapped_column(Integer)
    given_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now
    )

    @classmethod
    async def give(
        cls,
        session: AsyncSession,
        guild_id: int,
        giver_id: int,
        receiver_id: int,
        amount: int,
    ) -> Rep:
        """Record a rep transaction."""
        rep = cls(
            guild_id=guild_id,
            giver_id=giver_id,
            receiver_id=receiver_id,
            amount=amount,
        )
        session.add(rep)
        await session.commit()
        return rep

    @classmethod
    async def get_total_received(
        cls, session: AsyncSession, guild_id: int, user_id: int
    ) -> int:
        """Sum of all rep received by user_id in this guild."""
        result = await session.scalar(
            select(func.coalesce(func.sum(cls.amount), 0))
            .filter_by(guild_id=guild_id, receiver_id=user_id)
        )
        return int(result)

    @classmethod
    async def get_total_given(
        cls, session: AsyncSession, guild_id: int, user_id: int
    ) -> int:
        """Sum of all rep given by user_id in this guild."""
        result = await session.scalar(
            select(func.coalesce(func.sum(cls.amount), 0))
            .filter_by(guild_id=guild_id, giver_id=user_id)
        )
        return int(result)

    @classmethod
    async def get_biggest_fan(
        cls, session: AsyncSession, guild_id: int, user_id: int
    ) -> Optional[tuple[int, int]]:
        """Returns (giver_id, total) for the person who gave user_id the most positive rep.
        Returns None if no rep received."""
        result = await session.execute(
            select(cls.giver_id, func.sum(cls.amount).label("total"))
            .filter_by(guild_id=guild_id, receiver_id=user_id)
            .group_by(cls.giver_id)
            .order_by(func.sum(cls.amount).desc())
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        total = int(row.total)
        if total <= 0:
            return None
        return (row.giver_id, total)

    @classmethod
    async def get_hater(
        cls, session: AsyncSession, guild_id: int, user_id: int
    ) -> Optional[tuple[int, int]]:
        """Returns (giver_id, total) for the person who gave user_id the most negative rep.
        Returns None if no negative rep received."""
        result = await session.execute(
            select(cls.giver_id, func.sum(cls.amount).label("total"))
            .filter_by(guild_id=guild_id, receiver_id=user_id)
            .group_by(cls.giver_id)
            .order_by(func.sum(cls.amount).asc())
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        total = int(row.total)
        if total >= 0:
            return None  # No actual hater (all givers are net positive or zero)
        return (row.giver_id, total)

    @classmethod
    async def get_best_friend(
        cls, session: AsyncSession, guild_id: int, user_id: int
    ) -> Optional[tuple[int, int]]:
        """Returns (receiver_id, total) for the person user_id has given the most rep to.
        Returns None if user_id has given no rep."""
        result = await session.execute(
            select(cls.receiver_id, func.sum(cls.amount).label("total"))
            .filter_by(guild_id=guild_id, giver_id=user_id)
            .group_by(cls.receiver_id)
            .order_by(func.sum(cls.amount).desc())
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        total = int(row.total)
        if total <= 0:
            return None
        return (row.receiver_id, total)

    @classmethod
    async def get_nemesis(
        cls, session: AsyncSession, guild_id: int, user_id: int
    ) -> Optional[tuple[int, int]]:
        """Returns (receiver_id, total) for the person user_id has given the least (most negative) rep to.
        Returns None if user_id has given no negative rep."""
        result = await session.execute(
            select(cls.receiver_id, func.sum(cls.amount).label("total"))
            .filter_by(guild_id=guild_id, giver_id=user_id)
            .group_by(cls.receiver_id)
            .order_by(func.sum(cls.amount).asc())
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        total = int(row.total)
        if total >= 0:
            return None  # No nemesis (all recipients are net positive or zero)
        return (row.receiver_id, total)
