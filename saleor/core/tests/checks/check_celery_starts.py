"""Ensures Celery worker and Celery beat are both able to boot."""

import multiprocessing
import os.path
import socket
import tempfile
import time

from saleor.celeryconf import app

STARTUP_TIMEOUT_SECONDS = 30
PING_TIMEOUT_SECONDS = 1
WORKER_NAME = f"celery-start-check@{socket.gethostname()}"


def run_celery_worker(schedule_filename: str) -> None:
    app.worker_main(
        [
            "worker",
            "--loglevel=info",
            f"--hostname={WORKER_NAME}",
            # Run beat alongside the Celery worker so we can test both
            "--beat",
            # Create a state file for schedules
            f"--schedule={schedule_filename}",
        ]
    )


def wait_until_ready(worker_process: multiprocessing.Process) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if not worker_process.is_alive():
            raise RuntimeError("Celery worker stopped before it became ready.")

        responses = app.control.inspect(
            destination=[WORKER_NAME], timeout=PING_TIMEOUT_SECONDS
        ).ping()
        if responses is not None:
            assert responses == {WORKER_NAME: {"ok": "pong"}}
            return

        time.sleep(0.1)

    raise TimeoutError(
        f"Celery worker did not become ready within {STARTUP_TIMEOUT_SECONDS}s."
    )


def main() -> None:
    if not app.conf.broker_url:
        raise RuntimeError("CELERY_BROKER_URL must be configured to run this check.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        schedule_filename = os.path.join(tmp_dir, "celerybeat-schedule")
        worker_process = multiprocessing.Process(
            target=run_celery_worker,
            args=(schedule_filename,),
        )
        worker_process.start()

        try:
            wait_until_ready(worker_process)
        finally:
            worker_process.terminate()
            worker_process.join(timeout=PING_TIMEOUT_SECONDS)
            if worker_process.is_alive():
                worker_process.kill()
                worker_process.join()


if __name__ == "__main__":
    main()
