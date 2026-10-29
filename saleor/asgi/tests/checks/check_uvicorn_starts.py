"""Ensures that uvicorn and Saleor are able to start.

This is done by starting uvicorn in a subprocess, and then trying to send
a simple GraphQL query once the server is up (determined using ``/health/``)
"""

import multiprocessing
import os
import socket
import time

import django
import requests
import uvicorn
from django.conf import settings
from django.contrib.sites.models import Site

STARTUP_TIMEOUT_SECONDS = 30


def initialize_site() -> None:
    """Recreates the site if it's not available.

    This allows to repair the database when tests delete the site
    (when reusing the DB from `pytest --reuse-db`).
    """

    if settings.DEBUG is not True:
        raise AssertionError("Cannot run this file without DEBUG=true")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
    django.setup()

    from saleor.site.models import SiteSettings

    site, _ = Site.objects.get_or_create(
        pk=settings.SITE_ID,
        defaults={"name": "example.com", "domain": "example.com"},
    )
    SiteSettings.objects.get_or_create(site=site)
    Site.objects.clear_cache()


def run_uvicorn(server_socket: socket.socket) -> None:
    config = uvicorn.Config("saleor.asgi:application", log_level="info")
    instance = uvicorn.Server(config).run(sockets=[server_socket])
    assert instance is None


def wait_until_healthy(
    server_process: multiprocessing.Process, health_url: str
) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if not server_process.is_alive():
            raise RuntimeError("Uvicorn stopped before it became healthy.")

        try:
            # nosemgrep: no-requests-lib
            response = requests.get(health_url, timeout=(2, 2))
        except requests.RequestException:
            time.sleep(0.1)
            continue

        if response.status_code == 200:
            return

        time.sleep(0.1)

    raise TimeoutError("Uvicorn did not become healthy within 30 seconds.")


def check_response(resp: requests.Response) -> None:
    if resp.status_code != 200:
        raise AssertionError(f"Unexpected status: {resp.status_code}")

    try:
        content = resp.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise AssertionError("Unexpected response body") from exc

    if not isinstance(content, dict) or content.get("data") != {"__typename": "Query"}:
        raise AssertionError(f"Unexpected response: {content}")


def main() -> None:
    initialize_site()

    server_socket = socket.create_server(("127.0.0.1", 0))
    addr, port = server_socket.getsockname()

    server_process = multiprocessing.Process(target=run_uvicorn, args=(server_socket,))
    server_process.start()
    server_socket.close()

    try:
        wait_until_healthy(server_process, f"http://{addr}:{port}/health/")

        # nosemgrep: no-requests-lib # this is an internal CI/CD check
        response = requests.post(
            f"http://{addr}:{port}/graphql/",
            json={"query": "{__typename}"},
            timeout=(2, 2),
        )
        check_response(response)
    finally:
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            server_process.kill()
            server_process.join()


if __name__ == "__main__":
    main()
