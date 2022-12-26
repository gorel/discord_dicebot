#!/usr/bin/env python3

import asyncio

import flask

from dicebot.app import app_sessionmaker
from dicebot.data.db.guild import Guild
from dicebot.web import FLASK_DEBUG, discord_client, flask_app, stytch_client

DISCORD_USER_ID_SESSION_KEY = "discord_user_id"
DISCORD_PROVIDER_VALUES_ID_KEY = "id"


class LoginForm:
    def __init__(self) -> None:
        self.errors = []

    async def validate(self) -> bool:
        if flask.request.method == "GET":
            return False

        try:
            resp = await stytch_client.oauth.authenticate_async(
                token=flask.request.form["token"]
            )
        except Exception as e:
            self.errors.append(str(e))
            return False

        discord_user_id = int(resp.provider_subject)
        flask.session[DISCORD_USER_ID_SESSION_KEY] = discord_user_id
        return True


class UpdateGuildForm:
    def __init__(self, guild: Guild) -> None:
        self.guild = guild
        self.errors = []

    async def validate(self) -> bool:
        if flask.request.method == "GET":
            return False

        # TODO: Update guild here

        return True


@flask_app.route("/login", methods=["GET", "POST"])
async def login():
    form = LoginForm()
    if await form.validate():
        return flask.redirect(flask.url_for("admin_list"))
    else:
        return flask.render_template("login.html", errors=form.errors)


@flask_app.route("/admin/list")
async def admin_list():
    async with app_sessionmaker() as session:
        db_guilds = await Guild.get_all(session)
        tasks = [discord_client.fetch_guild(g.id) for g in db_guilds]
        fetched_guilds = await asyncio.gather(*tasks)
        guild_names = {
            g_db.id: g_discord.name
            for g_db, g_discord in zip(db_guilds, fetched_guilds)
        }

    return flask.render_template(
        "admin_list.html", guilds=db_guilds, guild_names=guild_names
    )


@flask_app.route("/admin/<int:guild_id>", methods=["GET", "POST"])
async def admin(guild_id: int):
    async with app_sessionmaker() as session:
        db_guild = await Guild.get_or_none(session, guild_id)
        if db_guild is None:
            return flask.render_template("404.html"), 404
        fetched_guild = await discord_client.fetch_guild(db_guild.id)
        guild_name = fetched_guild.name

    # Verify the logged-in user is an admin
    discord_user_id = flask.session.get(DISCORD_USER_ID_SESSION_KEY)
    if discord_user_id not in {user.id for user in db_guild.admins}:
        return flask.redirect(flask.url_for("login"))

    form = UpdateGuildForm(db_guild)
    if await form.validate():
        return flask.render_template(
            "admin.html", guild=db_guild, guild_name=guild_name, success=True
        )
    else:
        return flask.render_template(
            "admin.html", guild=db_guild, guild_name=guild_name, errors=form.errors
        )


def main() -> None:
    flask_app.run(host="0.0.0.0", debug=FLASK_DEBUG)


if __name__ == "__main__":
    main()
