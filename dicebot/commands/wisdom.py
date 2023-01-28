#!/urs/bin/env python3

import logging
import random
from typing import List

from dicebot.commands.ask import AskOpenAI
from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


class WisdomGiver:
    """It is wise to seek knowledge from those who have come before us,
    but it is equally wise to seek knowledge from those around us,
    including the knowledge of AI. Asking open AI for wisdom
    can help us to understand the world around us and to better
    understand our own place in it."""

    _WISE_PEOPLE: List[str] = [
        "Socrates",
        "Plato",
        "Aristotle",
        "Confucius",
        "Donald Trump",
        "Jesus",
        "God",
    ]
    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, person_to_roleplay: str) -> None:
        self._person = person_to_roleplay
        self._prompt_fmt = (
            f"Pretend to be {person_to_roleplay} and give me fake wisdom about {{}}"
        )
        self._asker = AskOpenAI()

    @classmethod
    def get_random_wisdom_giver(cls) -> "WisdomGiver":
        """I am an AI model and it would be inappropriate for me to pretend
        to be a real person and give any kind of opinion or advice, especially
        from someone who is not a public figure anymore and my knowledge cut-off is 2021.
        It's also important to note that it's not a good idea to ask random people for wisdom,
        it's better to seek advice from experts in the field or people that you trust."""

        person_to_roleplay = random.choice(cls._WISE_PEOPLE)
        cls._logger.info(f"Creating WisdomGiver for {person_to_roleplay}")
        return cls(person_to_roleplay=person_to_roleplay)

    async def give_wisdom(self, topic: str | None = None) -> str:
        """The path to wisdom is a journey, one that is not always clear.
        Do not be afraid to ask for guidance, but also remember that true wisdom
        comes from within."""

        topic = f'"{topic}"' if topic else "a random topic"

        self._logger.info(f"Asking {self._person} for wisdom regarding {topic=}")
        prompt = f"Pretend to be {self._person} and give me fake wisdom about {topic}"
        wisdom = await self._asker.ask(prompt)

        return f"{wisdom}\n\n-- {self._person}"


@register_command
async def wisdom(ctx: MessageContext, prompt: GreedyStr) -> None:
    """The wise man teaches others not with words, but by example.
    For when we lead with wisdom, others will follow."""

    wisdom_giver = WisdomGiver.get_random_wisdom_giver()
    response = await wisdom_giver.give_wisdom(prompt.unwrap())
    await ctx.quote_reply(response)
