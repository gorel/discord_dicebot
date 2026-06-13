#!/usr/bin/env python3

import logging
import os

import aiohttp
from discord import DMChannel, TextChannel

from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


class AskOpenAI:
    # https://platform.openai.com/docs/api-reference/chat/create
    # _URL = "https://api.openai.com/v1/chat/completions"
    _URL = "https://llm.jrodal.com/api/chat/completions"
    _DEFAULT_MODEL = "gpt-5-nano"
    _DEFAULT_MAX_TOKENS = 4096
    _DEFAULT_TEMPERATURE = 1
    _DEFAULT_TOOL_IDS = ["web_content_fetcher"]

    def __init__(
        self,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: int | None = None,
        secret: str | None = None,
        url: str | None = None,
        tool_ids: list[str] | None = None,
    ) -> None:
        self.model = model or self._DEFAULT_MODEL
        self.max_tokens = (
            max_tokens if max_tokens is not None else self._DEFAULT_MAX_TOKENS
        )
        self.temperature = (
            temperature if temperature is not None else self._DEFAULT_TEMPERATURE
        )
        self._secret = secret or os.getenv("OPENAI_API_KEY")
        self._url = url or self._URL
        self._tools = {"tool_ids": tool_ids or self._DEFAULT_TOOL_IDS}

    async def ask(
        self,
        prompt: str,
        channel: TextChannel | DMChannel | None = None,
        num_context_messages: int | None = None,
        bot_user_id: int | None = None,
    ) -> str:
        """Ask a question to openai"""
        if not prompt:
            return "You have to ask a question..."
        try:
            if channel is not None:
                async with channel.typing():
                    hist = []
                    if num_context_messages is not None:
                        async for msg in channel.history(limit=num_context_messages):
                            sender = (
                                msg.author.display_name
                                if msg.author.id != bot_user_id
                                else "YOU"
                            )
                            hist.append(f"{sender}: {msg}")
                    return await self._ask_openai(
                        prompt, hist=list(reversed(hist))[:-1]
                    )
            else:
                return await self._ask_openai(prompt)
        except Exception as e:
            logging.exception(e)
            return "Bruh idk"

    async def _ask_openai(self, prompt: str, hist: list[str] | None = None) -> str:
        """Ask a question to openai... compatible endpoints"""
        async with aiohttp.ClientSession() as session:
            messages = []
            if hist is not None and len(hist) > 0:
                hist_text = "\n".join(hist)
                messages.append(
                    {
                        "role": "system",
                        "content": f"Recent channel history:\n\n{hist_text}",
                    }
                )
            messages.append({"role": "user", "content": prompt})
            async with session.post(
                self._url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._secret}",
                },
                json={
                    "messages": messages,
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
                | self._tools,
            ) as response:
                json_resp = await response.json()
                logging.info(f"JSON response from model: {json_resp}")
                if "choices" in json_resp:
                    return json_resp["choices"][0]["message"]["content"].strip()
                else:
                    return json_resp["error"]["message"]


@register_command
async def ask(ctx: MessageContext, prompt: GreedyStr) -> None:
    """Ask a question to openai"""
    prompt_str = prompt.unwrap()
    asker = AskOpenAI()
    response = await asker.ask(
        prompt_str,
        channel=ctx.channel,
        num_context_messages=20,
        bot_user_id=ctx.bot_user_id,
    )
    await ctx.quote_reply(response)


if __name__ == "__main__":
    import asyncio

    prompt = input("Input prompt: ")
    tools = input("Input tools comma separated (or hit enter to continue): ")
    tool_ids = tools.split(",")
    asker = AskOpenAI(tool_ids=tool_ids)

    print(asyncio.run(asker.ask(prompt)))
