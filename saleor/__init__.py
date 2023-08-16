import pillow_avif  # noqa: F401 # imported for side effects

from .celeryconf import app as celery_app

__all__ = ["celery_app"]
__version__ = "3.16.0-a.0"


class PatchedSubscriberExecutionContext(object):
    __slots__ = "exe_context", "errors"

    def __init__(self, exe_context):
        self.exe_context = exe_context
        self.errors = self.exe_context.errors

    def reset(self):
        self.errors = []

    def __getattr__(self, name):
        return getattr(self.exe_context, name)


_major, _minor, _ = __version__.split(".", 2)
schema_version = f"{_major}.{_minor}"
