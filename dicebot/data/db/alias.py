#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional, Sequence

from sqlalchemy import BigInteger, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild
    from dicebot.data.db.user import User

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
int_ix = Annotated[int, mapped_column(BigInteger, index=True)]


class Alias(Base):
    __tablename__ = "alias"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    added_by: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    key: Mapped[str]
    value: Mapped[str]

    # Relationships
    author: Mapped[User] = relationship("User", lazy="selectin")

    @classmethod
    async def get(
        cls, session: AsyncSession, guild: Guild, key: str
    ) -> Optional[Alias]:
        res = await session.scalars(
            select(Alias).filter_by(guild_id=guild.id, key=key).limit(1)
        )
        return res.one_or_none()

    @classmethod
    async def get_all(cls, session: AsyncSession, guild: Guild) -> Sequence[Alias]:
        res = await session.scalars(select(Alias).filter_by(guild_id=guild.id))
        return res.all()

    def __repr__(self) -> str:
        return f"Alias({self.id=}, {self.key=}, {self.value=})"
