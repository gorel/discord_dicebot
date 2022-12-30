#!/usr/bin/env python3

import os

from quart import flash, g, redirect, render_template, url_for

from dicebot.web import app_ctx, quart_app
from dicebot.web.forms import AddMacroForm, LoginForm, UpdateGuildForm
from dicebot.web.models import CombinedGuildContext, RelevantGuild


@quart_app.route("/login")
async def login():
    form = LoginForm()
    if await form.validate():
        await flash("Logged in successfully")
        return redirect(url_for("list"))
    else:
        return await render_template(
            "login.html",
            user=g.current_user,
            discord_oauth_link=os.getenv("DISCORD_OAUTH_LINK"),
        )


@quart_app.route("/list")
async def list():
    all_guilds = await CombinedGuildContext.get_all(app_ctx.session)
    relevant_guilds = await RelevantGuild.get_subset_from_list(
        g.current_user, all_guilds
    )

    return await render_template(
        "list.html", guilds=relevant_guilds, user=g.current_user
    )


@quart_app.route("/admin/<int:guild_id>", methods=["GET", "POST"])
async def admin(guild_id: int):
    ctx = await CombinedGuildContext.get(app_ctx.session, guild_id)
    if ctx is None:
        await flash(f"Server with id={guild_id} not found", "alert-danger")
        return await render_template("404.html"), 404

    # Verify the logged-in user is an admin
    if not await ctx.is_admin(g.current_user):
        await flash("You are not an admin of that server", "alert-danger")
        return redirect(url_for("list"))

    form = UpdateGuildForm(app_ctx.session, ctx.db)
    if await form.validate():
        await flash("Changes saved successfully", "alert-success")
        # Redirect to avoid possible form resubmission
        return redirect(url_for("admin", guild_id=guild_id))

    return await render_template(
        "admin.html",
        ctx=ctx,
        user=g.current_user,
    )


@quart_app.route("/macros/<int:guild_id>", methods=["GET", "POST"])
async def macros(guild_id: int):
    ctx = await CombinedGuildContext.get(app_ctx.session, guild_id)
    if ctx is None:
        return await render_template("404.html"), 404

    fetched_macros = await ctx.db.get_all_macros(app_ctx.session)

    # Verify the logged-in user is a member
    if not await ctx.is_member(g.current_user):
        await flash("You are not a member of this server", "alert-warning")
        return redirect(url_for("login"))

    form = AddMacroForm(app_ctx.session, ctx.db)
    if await form.validate():
        await flash(f"Added macro for {form.key}", "alert-success")
        # Redirect to avoid possible form resubmission
        return redirect(url_for("macros", guild_id=guild_id))

    return await render_template(
        "macros.html",
        ctx=ctx,
        fetched_macros=fetched_macros,
        user=g.current_user,
    )


def register_routes() -> None:
    """Dummy just so this module is successfully loaded"""
    pass
