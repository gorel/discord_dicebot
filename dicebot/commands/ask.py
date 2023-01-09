#!/urs/bin/env python3

import os

import aiohttp

from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext

# https://beta.openai.com/docs/api-reference/completions/create
URL = "https://api.openai.com/v1/completions"
MODEL = "text-davinci-003"
MAX_TOKENS = 2048
TEMPERATURE = 0.5
_openai_secret_key = os.getenv("OPENAI_API_KEY")


@register_command
async def ask(ctx: MessageContext, prompt: GreedyStr) -> None:
    """Ask a question to openai"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_openai_secret_key}",
            },
            json={
                "prompt": prompt.unwrap(),
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
            },
        ) as response:
            json_resp = await response.json()
            await ctx.quote_reply(json_resp["choices"][0]["text"].strip())
