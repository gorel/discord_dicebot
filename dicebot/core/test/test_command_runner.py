"""
Unit tests for CommandRunner in dicebot.core.command_runner
"""
import unittest
from unittest.mock import AsyncMock

from dicebot.core.command_runner import CommandRunner
from dicebot.data.types.message_context import MessageContext
from dicebot.test.utils import TestMessageContext


class TestCommandRunner(unittest.IsolatedAsyncioTestCase):
    async def test_builtin_command(self):
        """A registered command should be called when invoked"""
        # Define a dummy command
        async def dummy(ctx: MessageContext) -> None:
            await ctx.send("dummy called")

        # Create runner with only our dummy command
        runner = CommandRunner(cmds=[dummy])

        # Prepare context for '!dummy'
        ctx = TestMessageContext.get("!dummy")
        ctx.send = AsyncMock()
        ctx.guild.get_alias = AsyncMock(return_value=None)

        # Invoke
        await runner.call(ctx)

        # Assert dummy was called via ctx.send
        ctx.send.assert_awaited_once_with("dummy called")

    async def test_macro_fallback(self):
        """If no command found, fallback to macro"""
        runner = CommandRunner(cmds=[])

        # Prepare context for '!foobar'
        ctx = TestMessageContext.get("!foobar")
        ctx.send = AsyncMock()
        ctx.guild.get_alias = AsyncMock(return_value=None)
        # Simulate a macro object with a value attribute
        macro_obj = type("Macro", (), {"value": "macro value"})()
        ctx.guild.get_macro = AsyncMock(return_value=macro_obj)

        # Invoke
        await runner.call(ctx)

        # Assert macro value was sent
        ctx.send.assert_awaited_once_with("macro value")

    async def test_unknown_command_raises(self):
        """Unknown command and no macro should raise KeyError"""
        runner = CommandRunner(cmds=[])

        # Prepare context for '!unknown'
        ctx = TestMessageContext.get("!unknown")
        ctx.send = AsyncMock()
        ctx.guild.get_alias = AsyncMock(return_value=None)
        ctx.guild.get_macro = AsyncMock(return_value=None)

        # Invoke and expect KeyError
        with self.assertRaises(KeyError):
            await runner.call(ctx)