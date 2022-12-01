#!/usr/bin/env python3

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING, Annotated, Optional

from sqlalchemy import ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]
int_ix = Annotated[int, mapped_column(index=True)]
bool_f = Annotated[bool, mapped_column(default=False)]


class Rename(Base):
    class Type(IntEnum):
        GUILD = auto()
        CHAT = auto()

    __tablename__ = "rename"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    discord_user_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    rename_type: Mapped[int]
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
