#!/usr/bin/env python3

from __future__ import annotations
from typing import Optional

from sqlalchemy import BigInteger, Text, DateTime, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base


class Pun(Base):
    __tablename__ = "pun"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    setup: Mapped[str] = mapped_column(Text, nullable=False)
    punchline: Mapped[str] = mapped_column(Text, nullable=False)
    first_poster_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    posted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @classmethod
    async def get_by_punchline(
        cls, session: AsyncSession, guild_id: int, punchline: str
    ) -> Optional[Pun]:
        result = await session.scalars(
            select(Pun).filter_by(guild_id=guild_id, punchline=punchline)
        )
        return result.one_or_none()

    @classmethod
    async def add_or_get(
        cls, session: AsyncSession, guild_id: int, setup: str, punchline: str, first_poster_id: int
    ) -> Pun:
        pun = await cls.get_by_punchline(session, guild_id, punchline)
        if pun is None:
            pun = cls(
                guild_id=guild_id,
                setup=setup,
                punchline=punchline,
                first_poster_id=first_poster_id,
            )
            session.add(pun)
            await session.commit()
        return pun

    def __repr__(self) -> str:
        return (
            f"Pun(id={self.id}, guild_id={self.guild_id}, setup={self.setup!r}, "
            f"punchline={self.punchline!r}, first_poster_id={self.first_poster_id}, "
            f"posted_at={self.posted_at})"
        )