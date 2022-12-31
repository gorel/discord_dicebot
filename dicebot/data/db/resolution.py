#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated, Optional, Sequence

from sqlalchemy import BigInteger, ForeignKey, func, select, sql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
int_ix = Annotated[int, mapped_column(BigInteger, index=True)]
bool_t_sd = Annotated[bool, mapped_column(server_default=sql.true())]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class Resolution(Base):
    __tablename__ = "resolution"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    author_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    channel_id: Mapped[int] = mapped_column(BigInteger)
    msg: Mapped[str]
    frequency: Mapped[str]
    active: Mapped[bool_t_sd]
    created_at: Mapped[timestamp_now]

    # Methods
    @classmethod
    async def get_or_none(
        cls, session: AsyncSession, resolution_id: int
    ) -> Optional[Resolution]:
        return await session.get(cls, resolution_id)

    @classmethod
    async def get_all_for_user(
        cls, session: AsyncSession, author_id: int
    ) -> Sequence[Resolution]:
        res = await session.scalars(
            select(Resolution).filter_by(author_id=author_id, active=True)
        )
        return res.all()
