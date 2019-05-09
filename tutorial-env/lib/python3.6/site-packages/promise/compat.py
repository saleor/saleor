try:
    from inspect import iscoroutine
except ImportError:

    def iscoroutine(obj):  # type: ignore
        return False


try:
    from asyncio import Future, ensure_future  # type: ignore
except ImportError:

    class Future:  # type: ignore
        def __init__(self):
            raise Exception("You need asyncio for using Futures")

        def set_result(self):
            raise Exception("You need asyncio for using Futures")

        def set_exception(self):
            raise Exception("You need asyncio for using Futures")

    def ensure_future():  # type: ignore
        raise Exception("ensure_future needs asyncio for executing")


try:
    from .iterate_promise import iterate_promise
except (SyntaxError, ImportError):

    def iterate_promise(promise):  # type: ignore
        raise Exception('You need "yield from" syntax for iterate in a Promise.')
