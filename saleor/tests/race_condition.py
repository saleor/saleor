from functools import wraps
from unittest.mock import patch


class RaceConditionTrigger:
    def __init__(self, target, callback):
        self.target = target
        self.callback = callback
        self.has_been_called = False

    def __enter__(self):
        self.patched_function = patch(self.target)
        original_function, _ = self.patched_function.get_original()
        if type(original_function) is classmethod:
            # classmethod needs to have an initialized class. get_original
            # returns the direct handler to the classmethod. Calling it without class
            # produces "'classmethod' object is not callable" error
            target_class = self.patched_function.getter()
            target_method = self.patched_function.attribute
            original_function = getattr(target_class, target_method)

        self.patched_function.new = self.wrap(original_function)
        return self.patched_function.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.patched_function.__exit__(exc_type, exc_value, traceback)

    def wrap(self, function):
        @wraps(function)
        def _wrapper(*args, **kwargs):
            if self.has_been_called:
                return function(*args, **kwargs)
            self.has_been_called = True
            return self.exec_with_callback(function, *args, **kwargs)

        return _wrapper

    def exec_with_callback(self, function, *args, **kwargs):
        raise NotImplementedError


class RunBefore(RaceConditionTrigger):
    def exec_with_callback(self, function, *args, **kwargs):
        self.callback(*args, **kwargs)
        return function(*args, **kwargs)


class RunAfter(RaceConditionTrigger):
    def exec_with_callback(self, function, *args, **kwargs):
        result = function(*args, **kwargs)
        self.callback(*args, **kwargs)
        return result
