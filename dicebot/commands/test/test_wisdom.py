#!/usr/bin/env python3

from unittest.mock import Mock, patch

from dicebot.commands.wisdom import WisdomGiver, wisdom
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestAsk(DicebotTestCase):
    @patch("dicebot.commands.ask.AskOpenAI.ask")
    async def test_give_wisdom(self, mock_ask: Mock) -> None:
        person = "Dicebot"
        wisdom_giver = WisdomGiver(person)

        empty_prompt_wisdom = "wisdom for random topic"
        not_empty_prompt_wisdom = "wisdom for a specific topic"

        mock_ask.side_effect = (
            lambda x: empty_prompt_wisdom
            if "a random topic" in x
            else not_empty_prompt_wisdom
        )

        with self.subTest("prompt: None"):
            actual_response = await wisdom_giver.give_wisdom()
            self.assertEqual(f"{empty_prompt_wisdom}\n\n-- {person}", actual_response)

        with self.subTest("prompt: empty str"):
            actual_response = await wisdom_giver.give_wisdom("")
            self.assertEqual(f"{empty_prompt_wisdom}\n\n-- {person}", actual_response)

        with self.subTest("prompt: not empty"):
            actual_response = await wisdom_giver.give_wisdom("bruh")
            self.assertEqual(
                f"{not_empty_prompt_wisdom}\n\n-- {person}", actual_response
            )

    async def test_wisdom(self) -> None:
        expected_response = "lolol"
        ctx = TestMessageContext.get()
        with patch(
            "dicebot.commands.wisdom.WisdomGiver.give_wisdom",
            return_value=expected_response,
        ):
            await wisdom(ctx, GreedyStr("a b c"))
            ctx.quote_reply.assert_awaited_once_with(expected_response)
