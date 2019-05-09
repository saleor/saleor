# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Callable


class SyncExecutor(object):
    def wait_until_finished(self):
        # type: () -> None
        pass

    def clean(self):
        pass

    def execute(self, fn, *args, **kwargs):
        # type: (Callable, *Any, **Any) -> Any
        return fn(*args, **kwargs)
