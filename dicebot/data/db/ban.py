#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Annotated, Optional

from sqlalchemy import BigInteger, ForeignKey, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild
    from dicebot.data.db.user import User

# Special types to make the ORM models prettier
bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]
bool_f = Annotated[bool, mapped_column(default=False)]


class Ban(Base):
    __tablename__ = "ban"

    # Columns
    id: Mapped[bigint_pk]
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    bannee_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    banner_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    reason: Mapped[str]
    banned_at: Mapped[timestamp_now]
    banned_until: Mapped[datetime.datetime]
    acknowledged: Mapped[bool_f]
    voided: Mapped[bool_f]
    voided_early_at: Mapped[Optional[datetime.datetime]]

    # Methods
    @classmethod
    async def get_latest_unvoided_ban(
        cls, session: AsyncSession, guild: Guild, bannee: User
    ) -> Optional[Ban]:
        res = await session.scalars(
            select(cls)
            .filter_by(
                guild_id=guild.id, bannee_id=bannee.id, voided=False, acknowledged=False
            )
            .order_by(desc(cls.banned_until))
            .limit(1)
        )
        return res.one_or_none()

    @classmethod
    async def unban(cls, session: AsyncSession, guild: Guild, bannee: User) -> None:
        await session.execute(
            update(cls)
            .filter_by(guild_id=guild.id, bannee_id=bannee.id, voided=False)
            .filter(cls.banned_until >= datetime.datetime.now())
            .values(voided=True, voided_early_at=datetime.datetime.now())
        )

    def __repr__(self) -> str:
        return (
            f"Ban({self.id=}, {self.guild_id=}, {self.bannee_id=}, "
            f"{self.banner_id=}, {self.reason=}, {self.banned_at=}, "
            f"{self.banned_until=}, {self.voided=}, {self.voided_early_at=})"
        )
