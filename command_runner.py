#!/usr/bin/env python3

import logging
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    get_type_hints
)

import discord

import command
from message_context import MessageContext


CommandFunc = Callable[..., Awaitable[None]]
T = TypeVar("T")


DEFAULT_REGISTERED_COMMANDS = [
    command.roll,
    command.scoreboard,
    command.set_msg,
    command.rename,
    command.reset_roll,
    command.set_timeout,
    command.clear_stats,
    command.remindme,
    command.ban,
    command.unban,
    command.macro_add,
    command.macro_del,
    command.m,
]


class CommandRunner:
    def __init__(
        self,
        ctx: MessageContext,
        cmds: Optional[List[CommandFunc]] = None,
    ):
        self.ctx = ctx
        cmds = cmds or DEFAULT_REGISTERED_COMMANDS
        self.cmds = {cmd.__name__: cmd for cmd in cmds}

    def register(self, cmd: CommandFunc) -> None:
        self.cmds[cmd.__name__] = cmd

    @staticmethod
    def typify(typ: Type[T], value: str) -> Any:
        if "from_str" in dir(typ):
            # Classes explicitly set up with a from_str constructor
            # TODO - Not sure how to make this not sketchy
            return typ.from_str(value)
        else:
            # Assume typ takes a string constructor
            return typ(value)

    @staticmethod
    def typify_all(f: CommandFunc, args: List[str]) -> Dict[str, Any]:
        types = get_type_hints(f)

        # Validate that this is a function taking a MessageContext
        ctx_param = None
        for k,v in types.items():
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

        if len(parameters) > 0 and types[parameters[-1]] is command.GreedyStr:
            # This is -1 because the last argument will be part of the glob
            n = len(parameters) - 1
            args, glob = args[:n], args[n:]
            greedy_arg = " ".join(glob)
            args.append(greedy_arg)

        # Make sure *all* arguments are kwargs now
        typed_args = {
            k: CommandRunner.typify(types[k], v)
            # TODO: We implicitly rely on ctx being the first param here,
            # which isn't good style... it could break a function
            for k,v in zip(parameters, args)
        }
        return typed_args

    async def call(self, ctx: MessageContext) -> None:
        # Split args to prepare for dynamic dispatch
        argv = ctx.message.content.split(" ")
        funcname, args = argv[0], argv[1:]
        if funcname[0] != "!":
            raise ValueError("Called CommandRunner without leading `!`")
        funcname = funcname[1:]

        # Now try to call the referenced method
        try:
            func = self.cmds[funcname]
            prepared_args = CommandRunner.typify_all(func, args)
            args_str = ", ".join(args)
            logging.info(f"Calling {funcname}(ctx, {args_str}) successfully")
            await func(ctx, **prepared_args)
        except Exception as e:
            # TODO: More granular exception
            # TODO: Differentiate between unknown func, bad params, internal failure
            # TODO: Log helpful message to message.guild
            logging.error(f"Failed to call function: {funcname}(ctx, {args_str})")
            logging.error(f"{type(e)}: {e}")
            # Reraise to let server_context provide help content
            raise

    @staticmethod
    def helptext(f: CommandFunc, limit: Optional[int] = None) -> str:
        fname = f"!{f.__name__}"
        types = get_type_hints(f)
        argc = f.__code__.co_argcount
        args = f.__code__.co_varnames[:argc]
        if len(args) > 0 and types[args[0]] is MessageContext:
            args = args[1:]
        args_str = " ".join(f"<{arg}>" for arg in args)

        usage = ""
        if f.__doc__ and len(f.__doc__) > 0:
            doc = f.__doc__
            if limit and len(doc) > limit:
                doc = doc[:limit] + "..."
                usage = f": {doc}"
            else:
                usage = f":\n{doc}"
        return f"!{f.__name__} {args_str}{usage}"

