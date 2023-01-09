#!/usr/bin/env python3

from unittest.mock import patch

from dicebot.commands import ask
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestAsk(DicebotTestCase):
    @patch("dicebot.commands.ask.AskOpenAI._ask_openai")
    async def test_ask_open_ai(self, mock_ask_openai) -> None:
        asker = ask.AskOpenAI()

        with self.subTest("No prompt"):
            expected_response = "You have to ask a question..."
            mock_ask_openai.return_value = expected_response
            actual_response = await asker.ask("")
            self.assertEqual(expected_response, actual_response)

        with self.subTest("Valid prompt, no error"):
            expected_response = "1+1 = 2"
            mock_ask_openai.return_value = expected_response
            actual_response = await asker.ask("What is 1+1?")
            self.assertEqual(expected_response, actual_response)

        with self.subTest("valid prompt, error"):
            expected_response = "Bruh idk"
            mock_ask_openai.side_effect = ValueError("test case expected failure")
            actual_response = await asker.ask("What is 1+1?")
            self.assertEqual(expected_response, actual_response)

    async def test_ask(self) -> None:
        expected_response = "lolol"
        ctx = TestMessageContext.get()
        with patch(
            "dicebot.commands.ask.AskOpenAI.ask", return_value=expected_response
        ):
            await ask.ask(ctx, GreedyStr("a b c"))
            ctx.quote_reply.assert_awaited_once_with(expected_response)
