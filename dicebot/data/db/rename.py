#!/usr/bin/env python3

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING, Annotated, Optional

from sqlalchemy import BigInteger, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild

# Special types to make the ORM models prettier
bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]
bool_f = Annotated[bool, mapped_column(default=False)]


class Rename(Base):
    class Type(IntEnum):
        GUILD = auto()
        CHAT = auto()

    __tablename__ = "rename"

    # Columns
    id: Mapped[bigint_pk]
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    discord_user_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    rename_type: Mapped[bigint]
    rename_used: Mapped[bool_f]

    # Methods
    @classmethod
    async def get_last_winner(
        cls, session: AsyncSession, guild: Guild
    ) -> Optional[Rename]:
        res = await session.scalars(
            select(cls).filter_by(rename_type=cls.Type.GUILD, guild_id=guild.id)
        )
        return res.one_or_none()

    @classmethod
    async def get_last_loser(
        cls, session: AsyncSession, guild: Guild
    ) -> Optional[Rename]:
        res = await session.scalars(
            select(cls).filter_by(rename_type=cls.Type.CHAT, guild_id=guild.id)
        )
        return res.one_or_none()

    def __repr__(self) -> str:
        return (
            f"Rename({self.id=}, {self.guild_id=}, "
            f"{self.discord_user_id=}, {self.rename_type=}, {self.rename_used=})"
        )
