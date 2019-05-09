"""Pattern matching registry."""
from __future__ import absolute_import, unicode_literals

from re import match as rematch
from fnmatch import fnmatch

from .utils.compat import entrypoints
from .utils.encoding import bytes_to_str


class MatcherNotInstalled(Exception):
    """Matcher not installed/found."""

    pass


class MatcherRegistry(object):
    """Pattern matching function registry."""

    MatcherNotInstalled = MatcherNotInstalled
    matcher_pattern_first = ["pcre", ]

    def __init__(self):
        self._matchers = {}
        self._default_matcher = None

    def register(self, name, matcher):
        """Add matcher by name to the registry."""
        self._matchers[name] = matcher

    def unregister(self, name):
        """Remove matcher by name from the registry."""
        try:
            self._matchers.pop(name)
        except KeyError:
            raise self.MatcherNotInstalled(
                'No matcher installed for {}'.format(name)
            )

    def _set_default_matcher(self, name):
        """Set the default matching method.

        :param name: The name of the registered matching method.
            For example, `glob` (default), `pcre`, or any custom
            methods registered using :meth:`register`.

        :raises MatcherNotInstalled: If the matching method requested
            is not available.
        """
        try:
            self._default_matcher = self._matchers[name]
        except KeyError:
            raise self.MatcherNotInstalled(
                'No matcher installed for {}'.format(name)
            )

    def match(self, data, pattern, matcher=None, matcher_kwargs=None):
        """Call the matcher."""
        if matcher and not self._matchers.get(matcher):
            raise self.MatcherNotInstalled(
                'No matcher installed for {}'.format(matcher)
            )
        match_func = self._matchers[matcher or 'glob']
        if matcher in self.matcher_pattern_first:
            first_arg = bytes_to_str(pattern)
            second_arg = bytes_to_str(data)
        else:
            first_arg = bytes_to_str(data)
            second_arg = bytes_to_str(pattern)
        return match_func(first_arg, second_arg, **matcher_kwargs or {})


#: Global registry of matchers.
registry = MatcherRegistry()


"""
.. function:: match(data, pattern, matcher=default_matcher,
                    matcher_kwargs=None):

    Match `data` by `pattern` using `matcher`.

    :param data: The data that should be matched. Must be string.
    :param pattern: The pattern that should be applied. Must be string.
    :keyword matcher: An optional string representing the mathcing
        method (for example, `glob` or `pcre`).

        If :const:`None` (default), then `glob` will be used.

    :keyword matcher_kwargs: Additional keyword arguments that will be passed
        to the specified `matcher`.
    :returns: :const:`True` if `data` matches pattern,
        :const:`False` otherwise.

    :raises MatcherNotInstalled: If the matching method requested is not
        available.
"""
match = registry.match


"""
.. function:: register(name, matcher):
    Register a new matching method.

    :param name: A convience name for the mathing method.
    :param matcher: A method that will be passed data and pattern.
"""
register = registry.register


"""
.. function:: unregister(name):
    Unregister registered matching method.

    :param name: Registered matching method name.
"""
unregister = registry.unregister


def register_glob():
    """Register glob into default registry."""
    registry.register('glob', fnmatch)


def register_pcre():
    """Register pcre into default registry."""
    registry.register('pcre', rematch)


# Register the base matching methods.
register_glob()
register_pcre()

# Default matching method is 'glob'
registry._set_default_matcher('glob')


# Load entrypoints from installed extensions
for ep, args in entrypoints('kombu.matchers'):
    register(ep.name, *args)
