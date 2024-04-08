#!/usr/bin/env python3

import logging
import os

import aiohttp

from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


class AskOpenAI:
    # https://platform.openai.com/docs/api-reference/chat/create
    _URL = "https://api.openai.com/v1/chat/completions"
    _DEFAULT_MODEL = "gpt-3.5-turbo"
    _DEFAULT_MAX_TOKENS = 2048
    _DEFAULT_TEMPERATURE = 0.5

    def __init__(
        self,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: int | None = None,
        secret: str | None = None,
    ) -> None:
        self.model = model or self._DEFAULT_MODEL
        self.max_tokens = (
            max_tokens if max_tokens is not None else self._DEFAULT_MAX_TOKENS
        )
        self.temperature = (
            temperature if temperature is not None else self._DEFAULT_TEMPERATURE
        )
        self._secret = secret or os.getenv("OPENAI_API_KEY")

    async def ask(self, prompt: str) -> str:
        """Ask a question to openai"""
        if not prompt:
            return "You have to ask a question..."
        try:
            return await self._ask_openai(prompt)
        except Exception as e:
            logging.exception(e)
            return "Bruh idk"

    async def _ask_openai(self, prompt: str) -> str:
        """Ask a question to openai"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._secret}",
                },
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            ) as response:
                json_resp = await response.json()
                logging.info(f"JSON response from model: {json_resp}")
                if "choices" in json_resp:
                    return json_resp["choices"][0]["text"].strip()
                else:
                    return json_resp["error"]["message"]


@register_command
async def ask(ctx: MessageContext, prompt: GreedyStr) -> None:
    """Ask a question to openai"""
    prompt_str = prompt.unwrap()
    asker = AskOpenAI()
    response = await asker.ask(prompt_str)
    await ctx.quote_reply(response)
