#!/usr/bin/env python3

import logging

from dicebot.commands.ask import AskOpenAI

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler

LAZIER_PROMPT = "Summarize the following in fewer words, but definitely no more than 50 words:\n\n{}\n"


# make these lowercase because I'm too lazy to write good code
TLDRWL_TRIGGERS = (
    "tldr",
    "tldw",
    "tldl",
    "tldrwl",
    "tl;dr",
    "tl;dw",
    "tl;dl",
    "tl;drwl",
    "bro, i don't have time for this shit",
)


async def do_tldr_summary(content: str, splits: int = 1) -> str:
    logging.info("Getting message summary, this could take a while...")
    to_summarize = content
    asker = AskOpenAI(tool_ids=["web_content_fetcher"])
    for _ in range(splits):
        try:
            to_summarize = await asker.ask(LAZIER_PROMPT.format(to_summarize))
            logging.info(f"Done with message summary. {to_summarize=}")
        except Exception:
            return "On second thought, I don't have time for this shit."
    return f"TL;DR:\n{to_summarize}"


class TldrwlHandler(AbstractHandler):
    """Get a too long, didn't read/write/listen summary"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        content = ctx.message.content.lower()
        splits = content.split(" ")
        return (ctx.message.reference is not None and content in TLDRWL_TRIGGERS) or (
            len(splits) == 2 and splits[0] in TLDRWL_TRIGGERS and splits[1].isdigit()
        )

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # Appease pyright
        assert ctx.client.user is not None

        reference = ctx.message.reference
        # I don't think this can happen if should_handle works properly
        if not reference or not reference.message_id:
            logging.info("The message reference is missing...")
            return

        replied_message = await ctx.message.channel.fetch_message(reference.message_id)

        # This shouldn't happen, I just don't want to risk a scenario where
        # the bot says tldr, then the summary of that is tldr, and so on...
        # openai bill would go brrrrrrr
        if replied_message.author.id == ctx.message.id == ctx.client.user.id:
            logging.info("Bot tried to summarize itself - skipping...")
            return

        cowboy_eyes = self.get_emoji_by_name(ctx, "cowboy_eyes")
        if cowboy_eyes is not None:
            await ctx.message.add_reaction(cowboy_eyes)
        else:
            await ctx.quote_reply("Beep boop, I'll get right on that")

        count = 1
        splits = ctx.message.content.lower().split(" ")
        if len(splits) == 2 and splits[1].isdigit():
            count = min(int(splits[1]), 10)

        summary = await do_tldr_summary(replied_message.content, count)
        await ctx.quote_reply(summary)
