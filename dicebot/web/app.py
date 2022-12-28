#!/usr/bin/env python3

import asyncio
from typing import List, Optional, Tuple

import discord
import quart

from dicebot.app import app_sessionmaker
from dicebot.core.client import Client
from dicebot.data.db.guild import Guild
from dicebot.web import QUART_DEBUG, quart_app, stytch_client

DISCORD_USER_ID_SESSION_KEY = "discord_user_id"
DISCORD_PROVIDER_VALUES_ID_KEY = "id"
DISCORD_CLIENT: Client


class LoginForm:
    def __init__(self) -> None:
        self.errors = []

    async def validate(self) -> bool:
        if "token" not in quart.request.args:
            return False

        try:
            resp = await stytch_client.oauth.authenticate_async(
                token=quart.request.args["token"]
            )
        except Exception as e:
            self.errors.append(str(e))
            return False

        discord_user_id = int(resp.provider_subject)
        quart.session[DISCORD_USER_ID_SESSION_KEY] = discord_user_id
        return True


class UpdateGuildForm:
    def __init__(self, guild: Guild) -> None:
        self.guild = guild
        self.errors = []

    async def validate(self) -> bool:
        if quart.request.method == "GET":
            return False

        # TODO: Update guild here

        return True


@quart_app.before_serving
async def create_discord_client() -> None:
    global DISCORD_CLIENT
    DISCORD_CLIENT = await Client.get_and_login()


async def get_current_user() -> Optional[discord.User]:
    global DISCORD_CLIENT
    discord_user_id = quart.session.get(DISCORD_USER_ID_SESSION_KEY)
    if discord_user_id is None:
        return None

    cached = DISCORD_CLIENT.get_user(discord_user_id)
    return cached or await DISCORD_CLIENT.fetch_user(discord_user_id)


async def get_guild(guild_id: int) -> discord.Guild:
    global DISCORD_CLIENT
    cached = DISCORD_CLIENT.get_guild(guild_id)
    return cached or await DISCORD_CLIENT.fetch_guild(guild_id)


async def get_relevant_guilds(
    user: discord.User, guilds: List[Tuple[Guild, discord.Guild]]
) -> List[discord.Guild]:
    res = []
    for db_guild, discord_guild in guilds:
        admins = [u.id for u in db_guild.admins]
        if user.id in admins:
            res.append(discord_guild)
    return res


@quart_app.route("/login")
async def login():
    form = LoginForm()
    if await form.validate():
        return quart.redirect(quart.url_for("admin_list"))
    else:
        user = await get_current_user()
        return await quart.render_template("login.html", user=user, errors=form.errors)


@quart_app.route("/admin/list")
async def admin_list():
    global DISCORD_CLIENT
    async with app_sessionmaker() as session:
        db_guilds = await Guild.get_all(session)
        db_guild_map = {g.id: g for g in db_guilds}
        tasks = [get_guild(g.id) for g in db_guilds]
        fetched_guilds = await asyncio.gather(*tasks)
        fetched_guild_map = {g.id: g for g in fetched_guilds}
        combined_guilds = [
            (db_guild_map[gid], fetched_guild_map[gid]) for gid in db_guild_map
        ]

    # Subset to relevant guilds only if the user is logged in
    relevant_guilds = fetched_guilds
    user = await get_current_user()
    if user is not None:
        relevant_guilds = await get_relevant_guilds(user, combined_guilds)

    return await quart.render_template(
        "admin_list.html", guilds=relevant_guilds, user=user
    )


@quart_app.route("/admin/<int:guild_id>", methods=["GET", "POST"])
async def admin(guild_id: int):
    global DISCORD_CLIENT
    async with app_sessionmaker() as session:
        db_guild = await Guild.get_or_none(session, guild_id)
        if db_guild is None:
            return await quart.render_template("404.html"), 404
        fetched_guild = await DISCORD_CLIENT.fetch_guild(db_guild.id)

    # Verify the logged-in user is an admin
    discord_user_id = quart.session.get(DISCORD_USER_ID_SESSION_KEY)
    if discord_user_id not in {user.id for user in db_guild.admins}:
        return quart.redirect(quart.url_for("login"))

    form = UpdateGuildForm(db_guild)
    user = await get_current_user()
    if await form.validate():
        await quart.flash("Changes saved successfully", "alert-success")
        return await quart.render_template(
            "admin.html",
            db_guild=db_guild,
            fetched_guild=fetched_guild,
            user=user,
        )
    else:
        for error in form.errors:
            await quart.flash(error, "alert-danger")
        return await quart.render_template(
            "admin.html",
            db_guild=db_guild,
            fetched_guild=fetched_guild,
            errors=form.errors,
            user=user,
        )


def main() -> None:
    quart_app.run(host="0.0.0.0", debug=QUART_DEBUG)


if __name__ == "__main__":
    main()
