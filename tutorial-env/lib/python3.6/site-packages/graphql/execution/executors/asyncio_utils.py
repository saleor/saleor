from inspect import isasyncgen  # type: ignore
from asyncio import ensure_future, wait, CancelledError
from rx import AnonymousObservable


def asyncgen_to_observable(asyncgen, loop=None):
    def emit(observer):
        task = ensure_future(iterate_asyncgen(asyncgen, observer), loop=loop)

        def dispose():
            async def await_task():
                await task

            task.cancel()
            ensure_future(await_task(), loop=loop)

        return dispose

    return AnonymousObservable(emit)


async def iterate_asyncgen(asyncgen, observer):
    try:
        async for item in asyncgen:
            observer.on_next(item)
        observer.on_completed()
    except CancelledError:
        pass
    except Exception as e:
        observer.on_error(e)
