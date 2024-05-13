#!/usr/bin/env python3

import logging

from tldrwl.exception import TldrwlException
from tldrwl.summarize import Gpt35TurboTextSummarizer, Summarizer, TextSummarizer

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


class LazierSummarizer(Gpt35TurboTextSummarizer):
    def __init__(self) -> None:
        super().__init__(prompt_string=LAZIER_PROMPT)


class TldrwlHandler(AbstractHandler):
    """Get a too long, didn't read/write/listen summary"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return (
            ctx.message.reference is not None
            and ctx.message.content.lower() in TLDRWL_TRIGGERS
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

        await ctx.quote_reply("Beep boop, I'll get right on that")
        logging.info("Getting message summary, this could take a while...")
        try:
            summary = await Summarizer(
                text_summarizer=LazierSummarizer()
            ).summarize_async(replied_message.content)
            logging.info(
                f"Done with message summary. {summary=}, {summary.estimated_cost_usd=}"
            )
            await ctx.quote_reply(summary.text)
        except TldrwlException as e:
            logging.exception(e)
            await ctx.quote_reply("OpenAI isn't free. Summarize this yourself.")
        except Exception as e:
            logging.exception(e)
            await ctx.quote_reply("On second thought, I don't have time for this shit.")
