"""Code copied from Django Software Foundation (https://djangoproject.com/) which is licensed under the BSD 3-Clause.

Original code: https://github.com/django/django/blob/001c2f546b4053acb04f16d6b704f7b4fbca1c45/django/core/handlers/asgi.py

Modifications: we added a fix for a memory leak
(https://code.djangoproject.com/ticket/36700).

Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

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
