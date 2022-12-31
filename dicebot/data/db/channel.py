#!/usr/bin/env python3

from __future__ import annotations

from typing import Annotated

from sqlalchemy import BigInteger, ForeignKey, sql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
int_ix = Annotated[int, mapped_column(BigInteger, index=True)]
bool_t_sd = Annotated[bool, mapped_column(server_default=sql.true())]


class Channel(Base):
    __tablename__ = "channel"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    shame: Mapped[bool_t_sd]

    # Methods
    @classmethod
    async def get_or_create(
        cls, session: AsyncSession, channel_id: int, guild_id: int
    ) -> Channel:
        res = await session.get(cls, channel_id)
        if res is None:
            res = cls(id=channel_id, guild_id=guild_id)
            session.add(res)
            await session.commit()
        return res
