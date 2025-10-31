import asyncio

import django
from asgiref.sync import sync_to_async
from django.core import signals
from django.core.exceptions import RequestAborted
from django.core.handlers.asgi import ASGIHandler, get_script_prefix
from django.urls import set_script_prefix


def get_asgi_application():
    django.setup(set_prefix=False)
    return PatchedASGIHandler()


class PatchedASGIHandler(ASGIHandler):
    async def handle(self, scope, receive, send):
        """
        Handles the ASGI request. Called via the __call__ method.
        """  # noqa: D200, D212, D401
        # Receive the HTTP request body as a stream object.
        try:
            body_file = await self.read_body(receive)
        except RequestAborted:
            return
        # Request is complete and can be served.
        set_script_prefix(get_script_prefix(scope))
        await signals.request_started.asend(sender=self.__class__, scope=scope)
        # Get the request and check for basic issues.
        request, error_response = self.create_request(scope, body_file)
        if request is None:
            body_file.close()
            await self.send_response(error_response, send)  # type: ignore[arg-type]
            await sync_to_async(error_response.close)()  # type: ignore[union-attr]
            return

        async def process_request(request, send):
            response = await self.run_get_response(request)
            try:
                await self.send_response(response, send)
            except asyncio.CancelledError:
                # Client disconnected during send_response (ignore exception).
                pass

            return response

        # Try to catch a disconnect while getting response.
        tasks = [
            # Check the status of these tasks and (optionally) terminate them
            # in this order. The listen_for_disconnect() task goes first
            # because it should not raise unexpected errors that would prevent
            # us from cancelling process_request().
            asyncio.create_task(self.listen_for_disconnect(receive)),
            asyncio.create_task(process_request(request, send)),
        ]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        # Now wait on both tasks (they may have both finished by now).
        for task in tasks:
            if task.done():
                try:
                    task.result()
                except RequestAborted:
                    # Ignore client disconnects.
                    pass
                except AssertionError:
                    body_file.close()
                    raise
            else:
                # Allow views to handle cancellation.
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    # Task re-raised the CancelledError as expected.
                    pass

        try:
            response = tasks[1].result()
        except asyncio.CancelledError:
            await signals.request_finished.asend(sender=self.__class__)
        else:
            await sync_to_async(response.close)()

        # https://code.djangoproject.com/ticket/36700
        # Tasks need to be cleared to prevent cycles is memory. Task `self.listen_for_disconnect(receive)` always
        # ends with `RequestAborted()` when connection are closed.
        # Request aborted exception holds reference to frame witch `tasks` as local variable. If tasks are not cleared,
        # reference cycle is created: Task -> RequestAbortedException -> Traceback -> Frame -> Locals -> Task.
        tasks.clear()
        body_file.close()
