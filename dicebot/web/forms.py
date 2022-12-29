#!/usr/bin/env python3

import quart
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User
from dicebot.web import stytch_client
from dicebot.web.constants import DISCORD_USER_ID_SESSION_KEY


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
    def __init__(self, guild: Guild) -> None:
        self.guild = guild

    async def validate(self) -> bool:
        if quart.request.method == "GET":
            return False

        # TODO: Update guild here

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
