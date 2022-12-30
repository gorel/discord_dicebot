#!/usr/bin/env python3

from typing import Callable, Optional, Type, TypeVar

import pytz
import quart
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User
from dicebot.web import stytch_client
from dicebot.web.constants import DISCORD_USER_ID_SESSION_KEY

T = TypeVar("T")


class LoginForm:
    async def validate(self) -> bool:
        if "token" not in quart.request.args:
            return False

        try:
            resp = await stytch_client.oauth.authenticate_async(
                token=quart.request.args["token"]
            )
        except Exception as e:
            await quart.flash(str(e))
            return False

        discord_user_id = int(resp.provider_subject)
        quart.session[DISCORD_USER_ID_SESSION_KEY] = discord_user_id
        return True


class UpdateGuildForm:
    def __init__(self, session: AsyncSession, guild: Guild) -> None:
        self.session = session
        self.guild = guild

    def try_int(self, s: Optional[str]) -> Optional[int]:
        return self.try_into(int, s)

    def try_into(
        self, into_callable: Callable[[str], T], s: Optional[str]
    ) -> Optional[T]:
        try:
            if s is not None:
                return into_callable(s)
        except Exception:
            pass
        return None

    async def validate(self) -> bool:
        if quart.request.method == "GET":
            return False

        form = await quart.request.form
        allow_renaming = form.get("allow_renaming")
        current_renaming = self.guild.allow_renaming
        # Only display something if the setting *changed*
        if allow_renaming == "on" and not current_renaming:
            await quart.flash("allow_renaming ON")
            self.guild.allow_renaming = True
        elif allow_renaming is None and current_renaming:
            await quart.flash("allow_renaming OFF")
            self.guild.allow_renaming = False

        current_roll = self.try_int(form.get("current_roll"))
        if current_roll is not None:
            await quart.flash(f"Current roll set to {current_roll}")
            self.guild.current_roll = current_roll

        roll_timeout = self.try_int(form.get("roll_timeout"))
        if roll_timeout is not None:
            await quart.flash(f"Roll timeout set to {roll_timeout} hours")
            self.guild.roll_timeout = roll_timeout

        # Intentional truthy check to avoid empty form responses
        critical_success_msg = form.get("critical_success_msg")
        if critical_success_msg:
            await quart.flash(
                f"Critical success message set to '{critical_success_msg}'"
            )
            self.guild.critical_success_msg = critical_success_msg

        # Intentional truthy check to avoid empty form responses
        critical_failure_msg = form.get("critical_failure_msg")
        if critical_failure_msg:
            await quart.flash(
                f"Critical failure message set to '{critical_failure_msg}'"
            )
            self.guild.critical_failure_msg = critical_failure_msg

        gambling_limit = self.try_int(form.get("gambling_limit"))
        if gambling_limit is not None:
            await quart.flash(f"Gambling limit set to {gambling_limit}")
            self.guild.gambling_limit = gambling_limit

        disable_announcements = form.get("disable_announcements")
        current_announcements = self.guild.disable_announcements
        # Only display something if the setting *changed*
        if disable_announcements == "on" and not current_announcements:
            await quart.flash("disable_announcements ON")
            self.guild.disable_announcements = True
        elif disable_announcements is None and current_announcements:
            await quart.flash("disable_announcements OFF")
            self.guild.disable_announcements = False

        timezone_str = form.get("timezone")
        timezone = self.try_into(pytz.timezone, timezone_str)
        if timezone is not None:
            assert timezone_str is not None
            await quart.flash(f"Timezone set to '{timezone_str}'")
            self.guild.timezone = timezone_str

        reaction_threshold = self.try_int(form.get("reaction_threshold"))
        if reaction_threshold is not None:
            self.guild.reaction_threshold = reaction_threshold

        turboban_threshold = self.try_int(form.get("turboban_threshold"))
        if turboban_threshold is not None:
            self.guild.turboban_threshold = turboban_threshold

        await self.session.commit()
        return True


class AddMacroForm:
    def __init__(self, session: AsyncSession, guild: Guild) -> None:
        self.session = session
        self.guild = guild
        self.key = ""

    async def validate(self) -> bool:
        if quart.request.method == "GET":
            return False

        form = await quart.request.form
        key = form.get("key")
        value = form.get("value")
        if key is None or value is None:
            await quart.flash("Missing key or value within form")
            return False

        if " " in key:
            await quart.flash("Spaces not allowed in macro key")
            return False

        self.key = key
        author = await User.get_or_create(self.session, quart.g.current_user_id)
        await self.guild.add_macro(self.session, key, value, author)
        await self.session.commit()

        return True
