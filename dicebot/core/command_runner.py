#!/usr/bin/env python3

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, get_type_hints

from dicebot.core.import_witchcraft import import_submodules
from dicebot.core.register_command import REGISTERED_COMMANDS
from dicebot.data.types.bot_param import BotParam
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.protocols import typify_str

CommandFunc = Callable[..., Awaitable[None]]

# This is how we trick Python into loading *all* of the registered commands
# from the commands/ subdir. Is there a better way to do this? Probably.
# But I couldn't figure it out.
import_submodules("dicebot.commands")


class CommandRunner:
    def __init__(self, cmds: Optional[List[CommandFunc]] = None) -> None:
        cmds = cmds or REGISTERED_COMMANDS
        self.cmds = {cmd.__name__: cmd for cmd in cmds}

    def register(self, cmd: CommandFunc) -> None:
        self.cmds[cmd.__name__] = cmd

    @staticmethod
    def is_botparam_type(t: Any) -> bool:
        if hasattr(t, "__origin__"):
            return issubclass(t.__origin__, BotParam)
        return False

    @staticmethod
    async def typify_all(
        ctx: MessageContext, f: CommandFunc, args: List[str]
    ) -> Dict[str, Any]:
        types = get_type_hints(f)

        # Validate that this is a function taking a MessageContext
        ctx_param = None
        for k, v in types.items():
            if v is MessageContext:
                ctx_param = k

        if ctx_param is None:
            error = "Can only typify function with signature like:\n\t"
            error += "async def func(MessageContext, ...)"
            raise TypeError(error)

        # Remove those specialized arguments now
        del types[ctx_param]

        # TODO - Currently only handles GreedyStr as last arg
        # To handle in another position, we'd need to use something like
        # a regex matcher algorithm; not worth it currently
        argc = f.__code__.co_argcount
        parameters = list(f.__code__.co_varnames[:argc])
        for i in range(len(parameters)):
            if parameters[i] == ctx_param:
                del parameters[i]
                break

        # Also check if there are bot params we should disable
        parameters = [
            param
            for param in parameters
            if not CommandRunner.is_botparam_type(types[param])
        ]

        if len(parameters) > 0 and types[parameters[-1]] is GreedyStr:
            # This is -1 because the last argument will be part of the glob
            n = len(parameters) - 1
            args, glob = args[:n], args[n:]
            greedy_arg = " ".join(glob)
            args.append(GreedyStr(greedy_arg))

        # TODO: This is *maybe* a good idea, but if we want to support default
        # arguments, I think it could cause some additional headaches. For now,
        # let's just allow extraneous arguments.
        # if len(parameters) != len(args):
        #    raise ValueError(f"Have {len(parameters)} parameters bUt {len(args)} args given")

        # Make sure *all* arguments are kwargs now
        typed_args = {
            k: await typify_str(ctx, types[k], v)
            # TODO: We implicitly rely on ctx being the first param here,
            # which isn't good style... it could break a function
            for k, v in zip(parameters, args)
        }
        return typed_args

    async def call(self, ctx: MessageContext) -> None:
        # Split args to prepare for dynamic dispatch
        if ctx.message.content[0] != "!":
            raise ValueError("Called CommandRunner without leading `!`")
        message_no_exclaim = ctx.message.content[1:]
        message_no_spaces = message_no_exclaim.strip()  # Removing excess whitespaces
        argv = message_no_spaces.split(" ")
        funcname, args = argv[0].lower(), argv[1:]

        # Now try to call the referenced method
        args_str = ""
        try:
            func = self.cmds[funcname]
            prepared_args = await CommandRunner.typify_all(ctx, func, args)
            args_str = ", ".join(args)
            logging.info(f"Calling {funcname}(ctx, {args_str}) successfully")
            await func(ctx, **prepared_args)
        except KeyError:
            logging.error(f"Could not find function {funcname}")
            raise
        except Exception as e:
            # TODO: Log helpful message to message.guild
            logging.error(f"Failed to call function: {funcname}(ctx, {args_str})")
            logging.error(f"{type(e)}: {e}")
            # Reraise to let server context provide help content
            raise

    @staticmethod
    def helptext(f: CommandFunc, limit: Optional[int] = None) -> str:
        types = get_type_hints(f)
        argc = f.__code__.co_argcount
        args = f.__code__.co_varnames[:argc]

        args_str = ""
        if len(args) > 0 and types[args[0]] is MessageContext:
            args = args[1:]
            # If there are args, we prepend a space character since it will
            # start right after the function name (otherwise there's a somewhat
            # awkward extra space with helptext for param-less functions)
            if len(args) > 0:
                args_str = " "
        # This is going to look like some more witchcraft, but we have to fully
        # instantiate a generic and then check its __class__ attribute since
        # calling issubclass immediately tells us that types[arg] is not a class
        args_str += " ".join(
            f"<{arg}>" for arg in args if not CommandRunner.is_botparam_type(types[arg])
        )

        usage = ""
        if f.__doc__ and len(f.__doc__) > 0:
            doc = f.__doc__
            if limit and len(doc) > limit:
                doc = doc[:limit] + "..."
                usage = f": {doc}"
            else:
                usage = f":\n{doc}"
        return f"__!{f.__name__}__{args_str}{usage}"
