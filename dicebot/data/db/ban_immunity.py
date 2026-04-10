#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Annotated, Optional

from sqlalchemy import BigInteger, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild
    from dicebot.data.db.user import User

bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]


class BanImmunity(Base):
    __tablename__ = "ban_immunity"

    id: Mapped[bigint_pk]
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    user_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    granted_by: Mapped[bigint] = mapped_column(ForeignKey("discord_user.id"))
    immune_until: Mapped[datetime.datetime]

    @classmethod
    async def get_active(
        cls, session: AsyncSession, guild: Guild, user: User
    ) -> Optional[BanImmunity]:
        res = await session.scalars(
            select(cls)
            .filter_by(guild_id=guild.id, user_id=user.id)
            .filter(cls.immune_until > datetime.datetime.now())
            .order_by(cls.immune_until.desc())
            .limit(1)
        )
        return res.one_or_none()

    @classmethod
    async def grant(
        cls,
        session: AsyncSession,
        guild: Guild,
        user: User,
        granter: User,
        duration_seconds: int,
    ) -> BanImmunity:
        new_until = datetime.datetime.now() + datetime.timedelta(seconds=duration_seconds)
        existing = await cls.get_active(session, guild, user)
        if existing is not None:
            if existing.immune_until >= new_until:
                return existing
            existing.immune_until = new_until
            existing.granted_by = granter.id
            await session.commit()
            return existing
        immunity = cls(
            guild_id=guild.id,
            user_id=user.id,
            granted_by=granter.id,
            immune_until=new_until,
        )
        session.add(immunity)
        await session.commit()
        return immunity

    def __repr__(self) -> str:
        return (
            f"BanImmunity({self.id=}, {self.guild_id=}, {self.user_id=}, "
            f"{self.immune_until=})"
        )
