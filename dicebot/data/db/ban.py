#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated, Optional

from sqlalchemy import ForeignKey, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base
from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]
int_ix = Annotated[int, mapped_column(index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]
bool_f = Annotated[bool, mapped_column(default=False)]


class Ban(Base):
    __tablename__ = "ban"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    bannee_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    banner_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    reason: Mapped[str]
    banned_at: Mapped[timestamp_now]
    banned_until: Mapped[datetime.datetime]
    voided: Mapped[bool_f]
    voided_early_at: Mapped[Optional[datetime.datetime]]

    # Methods
    @classmethod
    async def get_latest_unvoided_ban(
        cls, session: AsyncSession, guild: Guild, bannee: User
    ) -> Optional[Ban]:
        res = await session.scalars(
            select(cls, func.max(cls.banned_until)).filter_by(
                guild_id=guild.id, bannee_id=bannee.id, voided=False
            )
        )
        return res.one_or_none()

    @classmethod
    async def unban(cls, session: AsyncSession, guild: Guild, bannee: User) -> None:
        await session.scalars(
            update(cls)
            .filter_by(guild_id=guild.id, bannee_id=bannee.id, voided=False)
            .filter(cls.banned_until >= datetime.datetime.now())
            .values(voided=True, voided_early_at=datetime.datetime.now())
        )
