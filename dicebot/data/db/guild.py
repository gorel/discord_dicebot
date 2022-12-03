#!/usr/bin/env python3

from __future__ import annotations

from typing import Annotated, Optional

import discord
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Table,
    case,
    delete,
    desc,
    func,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dicebot.data.db.ban import Ban
from dicebot.data.db.base import Base
from dicebot.data.db.feature import Feature
from dicebot.data.db.macro import Macro
from dicebot.data.db.rename import Rename
from dicebot.data.db.roll import Roll
from dicebot.data.db.user import User

# Special types to make the ORM models prettier
bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk_natural = Annotated[
    int, mapped_column(BigInteger, primary_key=True, autoincrement=False)
]
bool_f = Annotated[bool, mapped_column(default=False)]

DEFAULT_START_ROLL = 6
DEFAULT_ROLL_TIMEOUT_HOURS = 12
DEFAULT_REACTION_THRESHOLD = 5
DEFAULT_TURBOBAN_THRESHOLD_SECS = 300
DEFAULT_CRITICAL_SUCCESS_MSG = "critical success!"
DEFAULT_CRITICAL_FAILURE_MSG = "critical failure!"
DEFAULT_GUILD_TZ = "US/Pacific"


# Many-to-many assoc to link guilds to features
guild_feature_assoc = Table(
    "guild_feature_assoc",
    Base.metadata,
    Column("guild_id", ForeignKey("guild.id")),
    Column("feature_id", ForeignKey("feature.id")),
)
# Many-to-many assoc to link users to the guilds in which they are admins
user_guild_admin_assoc = Table(
    "user_guild_admin_assoc",
    Base.metadata,
    Column("discord_user_id", ForeignKey("discord_user.id")),
    Column("guild_id", ForeignKey("guild.id")),
)


class Guild(Base):
    __tablename__ = "guild"

    # Columns
    id: Mapped[bigint_pk_natural]
    is_dm: Mapped[bool_f]
    current_roll: Mapped[bigint] = mapped_column(default=DEFAULT_START_ROLL)
    roll_timeout: Mapped[bigint] = mapped_column(default=DEFAULT_ROLL_TIMEOUT_HOURS)
    critical_success_msg: Mapped[str] = mapped_column(
        default=DEFAULT_CRITICAL_SUCCESS_MSG
    )
    critical_failure_msg: Mapped[str] = mapped_column(
        default=DEFAULT_CRITICAL_FAILURE_MSG
    )
    timezone: Mapped[str] = mapped_column(default=DEFAULT_GUILD_TZ)
    allow_renaming: Mapped[bool_f]
    reaction_threshold: Mapped[bigint] = mapped_column(
        default=DEFAULT_REACTION_THRESHOLD
    )
    turboban_threshold: Mapped[bigint] = mapped_column(
        default=DEFAULT_TURBOBAN_THRESHOLD_SECS
    )

    # Relationships
    admins: Mapped[list[User]] = relationship(
        secondary=user_guild_admin_assoc, lazy="selectin"
    )
    features: Mapped[list[Feature]] = relationship(
        secondary=guild_feature_assoc, lazy="selectin"
    )

    # Methods
    async def unban(self, session: AsyncSession, target: User) -> None:
        await Ban.unban(session, self, target)

    async def get_macro(self, session: AsyncSession, key: str) -> Optional[Macro]:
        return await Macro.get(session, self, key)

    async def add_macro(
        self, session: AsyncSession, key: str, value: str, author: User
    ) -> None:
        old_macro = await self.get_macro(session, key)
        if old_macro is None:
            new_macro = Macro(
                guild_id=self.id, added_by=author.id, key=key, value=value
            )
            session.add(new_macro)
        else:
            old_macro.value = value

    async def add_chat_rename(self, session: AsyncSession, author: User) -> None:
        rename = Rename(
            guild_id=self.id,
            discord_user_id=author.id,
            rename_type=Rename.Type.CHAT,
        )
        session.add(rename)

    async def add_guild_rename(self, session: AsyncSession, author: User) -> None:
        rename = Rename(
            guild_id=self.id,
            discord_user_id=author.id,
            rename_type=Rename.Type.GUILD,
        )
        session.add(rename)

    async def roll_scoreboard_str(
        self,
        client: discord.Client,
        session: AsyncSession,
    ) -> str:
        # TODO: Probably a better way to do this with declarative ORM style
        records = await session.execute(
            select(
                Roll.discord_user_id,
                func.count(
                    case((Roll.actual_roll == Roll.target_roll, 1),
                    else_=0)
                    ).label("wins"),
                func.count(
                    case((Roll.actual_roll == Roll.target_roll - 1, 1),
                    else_=0)
                    ).label("losses"),
                func.count(
                    case((Roll.actual_roll == 1, 1),
                    else_=0)
                    ).label("ones"),
                func.count(Roll.discord_user_id).label("attempts"),
            )
            .filter_by(guild_id=self.id)
            .group_by(Roll.discord_user_id)
            .order_by(text("wins"), text("losses"), text("ones"), text("attempts"))
        )

        msg = "**Stats:**\n"
        record_strs = []
        # TODO: Put this in a nice table
        for record in records.all():
            user = client.get_user(record.discord_user_id)
            if not user:
                user = await client.fetch_user(record.discord_user_id)
            record_strs.append(
                f"\t- {user.name} {record.wins} wins, {record.losses} losses, "
                f"{record.ones} critical losses (rolled 1), {record.attempts} total rolls"
            )
        msg += "\n".join(record_strs)
        return msg

    async def ban_scoreboard_str(
        self, client: discord.Client, session: AsyncSession
    ) -> str:
        # TODO: Probably a better way to do this with declarative ORM style
        ban_records = await session.execute(
            select(Ban.bannee_id, func.count(Ban.bannee_id).label("ban_count"))
            .filter_by(guild_id=self.id)
            .group_by(Ban.bannee_id)
            .order_by(desc(text("ban_count")))
        )

        msg = "**Ban stats:**\n"
        record_strs = []
        for record in ban_records.all():
            user = client.get_user(record.bannee_id)
            if not user:
                user = await client.fetch_user(record.bannee_id)
            record_strs.append(
                f"\t- {user.name} has been banned {record.ban_count} times"
            )
        msg += "\n".join(record_strs)
        return msg

    async def clear_stats(self, session: AsyncSession) -> None:
        await session.scalars(delete(Roll).where(Roll.guild_id == self.id))
        await session.scalars(delete(Rename).where(Rename.guild_id == self.id))
        self.current_roll = DEFAULT_START_ROLL

    @classmethod
    async def get_or_create(
        cls, session: AsyncSession, guild_id: int, owner_id: int, is_dm: bool
    ) -> Guild:
        res = await session.get(cls, guild_id)
        if res is None:
            res = cls(id=guild_id, is_dm=is_dm)
            # Add the new guild owner as the only admin
            owner = await User.get_or_create(session, owner_id)
            res.admins.append(owner)
            session.add(res)
            await session.commit()
        return res

    @classmethod
    async def get_or_none(cls, session: AsyncSession, guild_id: int) -> Optional[Guild]:
        return await session.get(cls, guild_id)

    def __repr__(self) -> str:
        return f"Guild({self.id=}, {self.is_dm=})"
