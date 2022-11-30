#!/usr/bin/env python3

from __future__ import annotations

import datetime
from enum import IntEnum, auto
from typing import Annotated, Optional

import discord
from sqlalchemy import Column, ForeignKey, Table, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (Mapped, declarative_base, mapped_column,
                            relationship)

Base = declarative_base()

DEFAULT_START_ROLL = 6
DEFAULT_ROLL_TIMEOUT_HOURS = 12
DEFAULT_REACTION_THRESHOLD = 5
DEFAULT_TURBOBAN_THRESHOLD_SECS = 300
DEFAULT_CRITICAL_SUCCESS_MSG = "critical success!"
DEFAULT_CRITICAL_FAILURE_MSG = "critical failure!"
DEFAULT_GUILD_TZ = "US/Pacific"

# Special types to make the ORM models below prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]
int_pk_natural = Annotated[int, mapped_column(primary_key=True, autoincrement=False)]
int_ix = Annotated[int, mapped_column(index=True)]
timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]
bool_f = Annotated[bool, mapped_column(default=False)]


# Many-to-many assoc to link guilds to features
guild_feature_assoc = Table(
    "guild_feature_assoc",
    Base.metadata,
    Column("guild_id", ForeignKey("guild.id")),
    Column("feature_id", ForeignKey("feature.id")),
)


class DiscordUser(Base):
    __tablename__ = "discord_user"

    id: Mapped[int_pk_natural]
    birthday: Mapped[Optional[timestamp]]

    def is_today_birthday_of_user(self, guild_tz: datetime.tzinfo) -> bool:
        if self.birthday is None:
            return False

        now = datetime.datetime.now(guild_tz)
        target_datetime = self.birthday.replace(year=now.year)
        return target_datetime.date() == now.date()

    async def is_currently_banned(self, session: AsyncSession, guild_id: int) -> bool:
        latest_ban = await Ban.get_latest_unvoided_ban(
            session, guild_id, self.discord_id
        )
        return (
            latest_ban is not None and latest_ban.banned_until > datetime.datetime.now()
        )

    @classmethod
    async def get_or_create(cls, session: AsyncSession, discord_id: int) -> DiscordUser:
        res = await session.get(cls, discord_id)
        if res is None:
            res = cls(id=discord_id)
            session.add(res)
            await session.commit()
        return res

    @classmethod
    def get_id_from_mention(cls, s: str) -> int:
        if len(s) > 0 and s[0] == "<" and s[-1] == ">":
            s = s[1:-1]
        if len(s) > 0 and s[0:2] == "@!":
            s = s[2:]
        elif len(s) > 0 and s[0] == "@":
            # Sometimes there's a leading @ but no ! -- I don't know why
            # I think it has to do with whether the user data has been
            # loaded by the client already
            s = s[1:]
        return int(s)


class Guild(Base):
    __tablename__ = "guild"

    id: Mapped[int_pk_natural]
    is_dm: Mapped[bool_f]
    current_roll: Mapped[int] = mapped_column(default=DEFAULT_START_ROLL)
    roll_timeout: Mapped[int] = mapped_column(default=DEFAULT_ROLL_TIMEOUT_HOURS)
    critical_success_msg: Mapped[str] = mapped_column(
        default=DEFAULT_CRITICAL_SUCCESS_MSG
    )
    critical_failure_msg: Mapped[str] = mapped_column(
        default=DEFAULT_CRITICAL_FAILURE_MSG
    )
    timezone: Mapped[str] = mapped_column(default=DEFAULT_GUILD_TZ)
    allow_renaming: Mapped[bool_f]
    enabled_features: Mapped[list[Feature]] = relationship(
        secondary=guild_feature_assoc
    )
    reaction_threshold: Mapped[int] = mapped_column(default=DEFAULT_REACTION_THRESHOLD)
    turboban_threshold: Mapped[int] = mapped_column(
        default=DEFAULT_TURBOBAN_THRESHOLD_SECS
    )

    async def unban(self, session: AsyncSession, target: DiscordUser) -> None:
        await Ban.unban(session, self.id, target.discord_id)

    async def get_macro(self, session: AsyncSession, key: str) -> Optional[Macro]:
        return await Macro.get(session, self.id, key)

    async def add_macro(
        self, session: AsyncSession, key: str, value: str, author: DiscordUser
    ) -> None:
        old_macro = await self.get_macro(session, key)
        if old_macro is None:
            new_macro = Macro(
                guild_id=self.id, added_by=author.discord_id, key=key, value=value
            )
            session.add(new_macro)
        else:
            old_macro.value = value

    async def roll_scoreboard_str(
        self,
        client: discord.Client,
        session: AsyncSession,
    ) -> str:
        # TODO: Probably a better way to do this with declarative ORM style
        records = await session.scalars(
            select(
                Roll,
                func.count(func.IF(Roll.actual_roll == Roll.target_roll), 1, 0).label(
                    "wins"
                ),
                func.count(
                    func.IF(Roll.actual_roll == Roll.target_roll - 1), 1, 0
                ).label("losses"),
                func.count(func.IF(Roll.actual_roll == 1), 1, 0).label("ones"),
                func.count(Roll.discord_user_id).label("attempts"),
            )
            .filter_by(guild_id=self.id)
            .group_by(Roll.discord_user_id)
            .order_by("wins", "losses", "ones", "attempts")
        )

        msg = "**Stats:**\n"
        record_strs = []
        for record in records.all():
            user = client.get_user(record.bannee_id)
            if not user:
                user = await client.fetch_user(record.bannee_id)
            record_strs.append(
                f"\t- {user.name} {record.wins} W, {record.losses} L, {record.ones} ones ({record.attempts} rolls)"
            )
        msg += "\n".join(record_strs)
        return msg

    async def ban_scoreboard_str(
        self, client: discord.Client, session: AsyncSession
    ) -> str:
        # TODO: Probably a better way to do this with declarative ORM style
        ban_records = await session.scalars(
            select(Ban, func.count(Ban.guild_id).label("ban_count"))
            .filter_by(guild_id=self.id)
            .group_by(Ban.discord_user_id)
            .order_by(desc("ban_count"))
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

    @classmethod
    async def get_or_create(
        cls, session: AsyncSession, guild_id: int, is_dm: bool
    ) -> Guild:
        res = await session.get(cls, guild_id)
        if res is None:
            res = cls(id=guild_id, is_dm=is_dm)
            session.add(res)
            await session.commit()
        return res


class Macro(Base):
    __tablename__ = "macro"

    id: Mapped[int_pk]
    guild_id: Mapped[int_pk] = mapped_column(ForeignKey("guild.id"))
    added_by: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))
    key: Mapped[str]
    value: Mapped[str]

    author: Mapped[DiscordUser] = relationship("DiscordUser")

    @classmethod
    async def get(
        cls, session: AsyncSession, guild_id: int, key: str
    ) -> Optional[Macro]:
        res = await session.scalars(select(cls).filter_by(guild_id=guild_id, key=key))
        return res.one_or_none()


class Roll(Base):
    __tablename__ = "roll"

    id: Mapped[int_pk]
    guild_id: Mapped[int_pk] = mapped_column(ForeignKey("guild.id"))
    discord_user_id: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))
    actual_roll: Mapped[int]
    target_roll: Mapped[int]
    rolled_at: Mapped[timestamp]

    @classmethod
    async def get_last_roll(
        cls, session: AsyncSession, guild: Guild, discord_user: DiscordUser
    ) -> Optional[Roll]:
        res = await session.scalars(
            select(cls)
            .filter_by(guild_id=guild.id, discord_user_id=discord_user.id)
            .order_by(cls.id.desc())
        )
        return res.one_or_none()


class Rename(Base):
    class RenameType(IntEnum):
        GUILD = auto()
        CHAT = auto()

    __tablename__ = "rename"

    id: Mapped[int_pk]
    guild_id: Mapped[int_pk] = mapped_column(ForeignKey("guild.id"))
    discord_user_id: Mapped[int_pk] = mapped_column(
        ForeignKey("discord_user.discord_id")
    )
    rename_type: Mapped[int]
    rename_used: Mapped[bool_f]

    @classmethod
    async def get_last_winner(
        cls, session: AsyncSession, guild: Guild
    ) -> Optional[Rename]:
        res = await session.scalars(
            select(cls).filter_by(rename_type=cls.RenameType.GUILD, guild_id=guild.id)
        )
        return res.one_or_none()

    @classmethod
    async def get_last_loser(
        cls, session: AsyncSession, guild: Guild
    ) -> Optional[Rename]:
        res = await session.scalars(
            select(cls).filter_by(rename_type=cls.RenameType.CHAT, guild_id=guild.id)
        )
        return res.one_or_none()


class Feature(Base):
    __tablename__ = "feature"

    id: Mapped[int_pk]
    feature_name: Mapped[str]


class Ban(Base):
    __tablename__ = "ban"

    id: Mapped[int_pk]
    guild_id: Mapped[int_pk] = mapped_column(ForeignKey("guild.id"))
    bannee_id: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))
    banner_id: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))
    reason: Mapped[str]
    banned_at: Mapped[timestamp]
    banned_until: Mapped[timestamp]
    voided: Mapped[bool_f]
    voided_early_at: Mapped[Optional[timestamp]]

    @classmethod
    async def get_latest_unvoided_ban(
        cls, session: AsyncSession, guild: Guild, bannee: DiscordUser
    ) -> Optional[Ban]:
        res = await session.scalars(
            select(cls, func.max(cls.banned_until)).filter_by(
                guild_id=guild.id, bannee_id=bannee.id, voided=False
            )
        )
        return res.one_or_none()

    @classmethod
    async def unban(cls, session: AsyncSession, guild_id: int, bannee_id: int) -> None:
        await session.scalars(
            update(cls)
            .filter_by(guild_id=guild_id, bannee_id=bannee_id, voided=False)
            .filter(cls.banned_until >= datetime.datetime.now())
            .values(voided=True, voided_early_at=datetime.datetime.now())
        )


class ReactedMessage(Base):
    __tablename__ = "reacted_message"

    id: Mapped[int_pk]
    guild_id: Mapped[int_pk] = mapped_column(ForeignKey("guild.id"))
    msg_id: Mapped[int_ix]
    reacted_at: Mapped[timestamp]
    reaction_id: Mapped[int]

    @classmethod
    async def get_by_msg_and_reaction_id(
        cls, session: AsyncSession, msg_id: int, reaction_id: int
    ) -> Optional[ReactedMessage]:
        res = await session.scalars(
            select(cls).filter_by(msg_id=msg_id, reaction_id=reaction_id)
        )
        return res.one_or_none()
