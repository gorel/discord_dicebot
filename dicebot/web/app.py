#!/usr/bin/env python3

import asyncio

import quart

from dicebot.app import app_sessionmaker
from dicebot.core.client import Client
from dicebot.data.db.guild import Guild
from dicebot.web import QUART_DEBUG, quart_app, stytch_client

DISCORD_USER_ID_SESSION_KEY = "discord_user_id"
DISCORD_PROVIDER_VALUES_ID_KEY = "id"


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


@quart_app.route("/login")
async def login():
    form = LoginForm()
    if await form.validate():
        return quart.redirect(quart.url_for("admin_list"))
    else:
        return await quart.render_template("login.html", errors=form.errors)


@quart_app.route("/admin/list")
async def admin_list():
    async with app_sessionmaker() as session:
        discord_client = await Client.get_and_login()
        db_guilds = await Guild.get_all(session)
        tasks = [discord_client.fetch_guild(g.id) for g in db_guilds]
        fetched_guilds = await asyncio.gather(*tasks)
        guild_names = {
            g_db.id: g_discord.name
            for g_db, g_discord in zip(db_guilds, fetched_guilds)
        }

    # Subset to relevant guilds only if the user is logged in
    discord_user_id = quart.session.get(DISCORD_USER_ID_SESSION_KEY)
    relevant_guilds = db_guilds
    if discord_user_id is not None:
        relevant_guilds = [g for g in db_guilds if discord_user_id in g.admins]

    return await quart.render_template(
        "admin_list.html", guilds=relevant_guilds, guild_names=guild_names
    )


@quart_app.route("/admin/<int:guild_id>", methods=["GET", "POST"])
async def admin(guild_id: int):
    async with app_sessionmaker() as session:
        discord_client = await Client.get_and_login()
        db_guild = await Guild.get_or_none(session, guild_id)
        if db_guild is None:
            return await quart.render_template("404.html"), 404
        fetched_guild = await discord_client.fetch_guild(db_guild.id)
        guild_name = fetched_guild.name

    # Verify the logged-in user is an admin
    discord_user_id = quart.session.get(DISCORD_USER_ID_SESSION_KEY)
    if discord_user_id not in {user.id for user in db_guild.admins}:
        return quart.redirect(quart.url_for("login"))

    form = UpdateGuildForm(db_guild)
    if await form.validate():
        return await quart.render_template(
            "admin.html", guild=db_guild, guild_name=guild_name, success=True
        )
    else:
        return await quart.render_template(
            "admin.html", guild=db_guild, guild_name=guild_name, errors=form.errors
        )


def main() -> None:
    quart_app.run(host="0.0.0.0", debug=QUART_DEBUG)


if __name__ == "__main__":
    main()
