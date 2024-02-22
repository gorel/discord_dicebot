#!/usr/bin/env python3

import datetime

from dicebot.commands import ban, giffer
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.reaction.abstract_reaction_handler import AbstractReactionHandler


class KekwReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "kekw"

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # Appease pyright
        assert ctx.reaction is not None
        assert ctx.reactor is not None
        assert not isinstance(ctx.reaction.emoji, str)

        # Check if this was *really* funny
        current_date = datetime.datetime.now()
        now = current_date.replace(tzinfo=datetime.timezone.utc)
        elapsed = now - ctx.reaction.message.created_at
        turbo_kekw = elapsed.total_seconds() <= ctx.guild.turbo_reaction_threshold

        if turbo_kekw:
            emojis = {e.name: f"<:{e.name}:{e.id}>" for e in ctx.client.emojis}
            turbo = ["T_", "U_", "R_", "B_", "O_"]
            turbo_str = "".join(emojis[s] for s in turbo)
            kekw = ["K_", "E_", "K_", "W_"]
            kekw_str = "".join(emojis[s] for s in kekw)
            turbo_msg = f"{turbo_str} {kekw_str}"
            await ctx.quote_reply(turbo_msg, silent=False)
            gif_url = await giffer.get_random_gif_url("kekw")
            if gif_url is not None:
                await ctx.quote_reply(gif_url, silent=False)

        # If the user is banned, unban them early
        if await ctx.author.is_currently_banned(ctx.session, ctx.guild):
            await ctx.quote_reply("That's good stuff, I'm unbanning you early.")
            discord_user = await User.get_or_create(ctx.session, ctx.author_id)
            await ban.unban_internal(
                ctx, discord_user, f"<@{ctx.author_id}> has been unbanned early."
            )
