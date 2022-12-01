#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Annotated, Optional

from sqlalchemy import ForeignKey, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild
    from dicebot.data.db.user import User

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]
int_ix = Annotated[int, mapped_column(index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class Roll(Base):
    __tablename__ = "roll"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    discord_user_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    actual_roll: Mapped[int]
    target_roll: Mapped[int]
    rolled_at: Mapped[timestamp_now]

    # Methods
    @classmethod
    async def get_last_roll(
        cls, session: AsyncSession, guild: Guild, discord_user: User
    ) -> Optional[Roll]:
        res = await session.scalars(
            select(cls)
            .filter_by(guild_id=guild.id, discord_user_id=discord_user.id)
            .order_by(cls.id.desc())
        )
        return res.one_or_none()