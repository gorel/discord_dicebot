#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Annotated, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.ban import Ban
from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild


# Special types to make the ORM models prettier
int_pk_natural = Annotated[int, mapped_column(primary_key=True, autoincrement=False)]


class User(Base):
    __tablename__ = "discord_user"

    # Columns
    id: Mapped[int_pk_natural]
    birthday: Mapped[Optional[datetime.datetime]]

    # Methods
    def is_today_birthday_of_user(self, guild_tz: datetime.tzinfo) -> bool:
        if self.birthday is None:
            return False

        now = datetime.datetime.now(guild_tz)
        target_datetime = self.birthday.replace(year=now.year)
        return target_datetime.date() == now.date()

    def is_admin_of(self, guild: Guild) -> bool:
        return self in guild.admins

    def as_mention(self) -> str:
        """Returns a representation that can be sent to a channel and will act as a mention"""
        return f"<@{self.id}>"

    async def is_currently_banned(self, session: AsyncSession, guild: Guild) -> bool:
        latest_ban = await Ban.get_latest_unvoided_ban(session, guild, self)
        return (
            latest_ban is not None and latest_ban.banned_until > datetime.datetime.now()
        )

    @classmethod
    async def get_or_create(cls, session: AsyncSession, discord_id: int) -> User:
        res = await session.get(cls, discord_id)
        if res is None:
            res = cls(id=discord_id)
            session.add(res)
            await session.commit()
        return res

    @classmethod
    async def load_from_cmd_str(cls, session: AsyncSession, cmd_str: str) -> int:
        if len(cmd_str) > 0 and cmd_str[0] == "<" and cmd_str[-1] == ">":
            cmd_str = cmd_str[1:-1]
        if len(cmd_str) > 0 and cmd_str[0:2] == "@!":
            cmd_str = cmd_str[2:]
        elif len(cmd_str) > 0 and cmd_str[0] == "@":
            # Sometimes there's a leading @ but no ! -- I don't know why
            # I think it has to do with whether the user data has been
            # loaded by the client already
            cmd_str = cmd_str[1:]
        discord_id = int(cmd_str)
        return await cls.get_or_create(session, discord_id)
