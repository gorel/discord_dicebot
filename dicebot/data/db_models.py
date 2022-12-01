#!/usr/bin/env python3

from __future__ import annotations

import datetime
from enum import IntEnum, auto
from typing import Annotated, Optional

import discord
from sqlalchemy import (Column, ForeignKey, Table, desc, func, select, text,
                        update)
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
timestamp_now = Annotated[
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
# Many-to-many assoc to link users to the guilds in which they are admins
user_guild_admin_assoc = Table(
    "user_guild_admin_assoc",
    Base.metadata,
    Column("discord_user_id", ForeignKey("discord_user.id")),
    Column("guild_id", ForeignKey("guild.id")),
)


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


class Guild(Base):
    __tablename__ = "guild"

    # Columns
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
    reaction_threshold: Mapped[int] = mapped_column(default=DEFAULT_REACTION_THRESHOLD)
    turboban_threshold: Mapped[int] = mapped_column(
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
                guild_id=self.id, added_by=author.discord_id, key=key, value=value
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

    async def add_guild_rename(
        self, session: AsyncSession, author: User
    ) -> None:
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
            .order_by(text("wins"), text("losses"), text("ones"), text("attempts"))
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


class Macro(Base):
    __tablename__ = "macro"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    added_by: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    key: Mapped[str]
    value: Mapped[str]

    # Relationships
    author: Mapped[User] = relationship("User", lazy="selectin")

    # Methods
    @classmethod
    async def get(
        cls, session: AsyncSession, guild: Guild, key: str
    ) -> Optional[Macro]:
        res = await session.scalars(select(Macro).filter_by(guild_id=guild.id, key=key))
        return res.one_or_none()


class Roll(Base):
    __tablename__ = "roll"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    discord_user_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    actual_roll: Mapped[int]
    target_roll: Mapped[int]
    rolled_at: Mapped[timestamp_now]

    # Methods
    @classmethod
    async def get_last_roll(
        cls, session: AsyncSession, guild: Guild, discord_user: User
    ) -> Optional[Roll]:
        res = await session.scalars(
            select(cls)
            .filter_by(guild_id=guild.id, discord_user_id=discord_user.id)
            .order_by(cls.id.desc())
        )
        return res.one_or_none()


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


class Feature(Base):
    # TODO: Use enums to define features and load them on setup/create_all
    __tablename__ = "feature"

    # Columns
    id: Mapped[int_pk]
    feature_name: Mapped[str]

    # Methods
    @classmethod
    async def get_or_create(cls, session: AsyncSession, feature_name: str) -> Feature:
        res = await session.scalars(select(cls).filter_by(feature_name=feature_name))
        res = res.one_or_none()
        if res is None:
            res = cls(feature_name=feature_name)
            session.add(res)
            await session.commit()
        return res


class Ban(Base):
    __tablename__ = "ban"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    bannee_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    banner_id: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    reason: Mapped[str]
    banned_at: Mapped[timestamp_now]
    banned_until: Mapped[datetime.datetime]
    voided: Mapped[bool_f]
    voided_early_at: Mapped[Optional[datetime.datetime]]

    # Methods
    @classmethod
    async def get_latest_unvoided_ban(
        cls, session: AsyncSession, guild: Guild, bannee: User
    ) -> Optional[Ban]:
        res = await session.scalars(
            select(cls, func.max(cls.banned_until)).filter_by(
                guild_id=guild.id, bannee_id=bannee.id, voided=False
            )
        )
        return res.one_or_none()

    @classmethod
    async def unban(
        cls, session: AsyncSession, guild: Guild, bannee: User
    ) -> None:
        await session.scalars(
            update(cls)
            .filter_by(guild_id=guild.id, bannee_id=bannee.id, voided=False)
            .filter(cls.banned_until >= datetime.datetime.now())
            .values(voided=True, voided_early_at=datetime.datetime.now())
        )


class ReactedMessage(Base):
    __tablename__ = "reacted_message"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    msg_id: Mapped[int_ix]
    reacted_at: Mapped[timestamp_now]
    reaction_id: Mapped[int]

    # Methods
    @classmethod
    async def get_by_msg_and_reaction_id(
        cls, session: AsyncSession, msg_id: int, reaction_id: int
    ) -> Optional[ReactedMessage]:
        res = await session.scalars(
            select(cls).filter_by(msg_id=msg_id, reaction_id=reaction_id)
        )
        return res.one_or_none()
