#!/usr/bin/env python3

import logging

from tldrwl.exception import TldrwlException
from tldrwl.summarize import ChatCompletionsTextSummarizer, Summarizer

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
    for _ in range(splits):
        try:
            summary = await Summarizer(
                text_summarizer=LazierSummarizer()
            ).summarize_async(to_summarize)
            logging.info(
                f"Done with message summary. {summary=}, {summary.estimated_cost_usd=}"
            )
            to_summarize = summary.text
        except TldrwlException as e:
            logging.exception(e)
            return "OpenAI isn't free. Summarize this yourself."
        except Exception as e:
            return "On second thought, I don't have time for this shit."
    return f"TL;DR:\n{to_summarize}"


class LazierSummarizer(ChatCompletionsTextSummarizer):
    def __init__(self) -> None:
        super().__init__(prompt_string=LAZIER_PROMPT)


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
