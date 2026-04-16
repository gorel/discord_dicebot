#!/usr/bin/env python3

from __future__ import annotations

import datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Optional

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild

bigint = Annotated[int, mapped_column(BigInteger)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]


class EventType(str, Enum):
    DOUBLE_BAN = "double_ban"
    LUCKY_HOUR = "lucky_hour"
    CURSE_DAY = "curse_day"
    BLESSING_DAY = "blessing_day"
    TURBO_DAY = "turbo_day"


class ActiveEvent(Base):
    __tablename__ = "active_event"
    __table_args__ = (UniqueConstraint("guild_id", name="uq_active_event_guild"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    event_type: Mapped[str]
    started_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now
    )
    expires_at: Mapped[datetime.datetime]

    @property
    def event_type_enum(self) -> EventType:
        return EventType(self.event_type)

    @classmethod
    async def get_current(
        cls, session: AsyncSession, guild_id: int
    ) -> Optional[ActiveEvent]:
        """Return the active event for this guild, or None if none/expired."""
        res = await session.scalars(
            select(cls)
            .filter_by(guild_id=guild_id)
            .filter(cls.expires_at > datetime.datetime.now())
            .order_by(cls.expires_at.desc())
            .limit(1)
        )
        return res.one_or_none()

    def __repr__(self) -> str:
        return (
            f"ActiveEvent({self.id=}, {self.guild_id=}, {self.event_type=}, "
            f"{self.expires_at=})"
        )
