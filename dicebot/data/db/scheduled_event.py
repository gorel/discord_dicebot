#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Annotated, Optional, Sequence

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    pass

bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]


class ScheduledEvent(Base):
    __tablename__ = "scheduled_event"

    id: Mapped[bigint_pk]
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    channel_id: Mapped[bigint]
    name: Mapped[str]
    event_time: Mapped[datetime.datetime]
    message_id: Mapped[Optional[bigint]]

    @classmethod
    async def get_by_id(cls, session: AsyncSession, event_id: int) -> Optional[ScheduledEvent]:
        return await session.get(cls, event_id)

    @classmethod
    async def get_by_message_id(cls, session: AsyncSession, message_id: int) -> Optional[ScheduledEvent]:
        res = await session.scalars(select(cls).filter_by(message_id=message_id).limit(1))
        return res.one_or_none()

    @classmethod
    async def get_all_for_guild(cls, session: AsyncSession, guild_id: int) -> Sequence[ScheduledEvent]:
        res = await session.scalars(select(cls).filter_by(guild_id=guild_id))
        return res.all()

    @classmethod
    async def get_upcoming(cls, session: AsyncSession, guild_id: int) -> Sequence[ScheduledEvent]:
        now = datetime.datetime.utcnow()
        res = await session.scalars(
            select(cls)
            .filter(cls.guild_id == guild_id, cls.event_time > now)
            .order_by(cls.event_time)
        )
        return res.all()


class ScheduledEventSignup(Base):
    __tablename__ = "scheduled_event_signup"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_signup"),)

    id: Mapped[bigint_pk]
    event_id: Mapped[bigint_ix] = mapped_column(ForeignKey("scheduled_event.id"))
    user_id: Mapped[bigint]

    @classmethod
    async def get_all_for_event(cls, session: AsyncSession, event_id: int) -> Sequence[ScheduledEventSignup]:
        res = await session.scalars(select(cls).filter_by(event_id=event_id))
        return res.all()
