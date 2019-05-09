# Necessary for static type checking
if False:  # flake8: noqa
    from .source import Source
    from typing import Any

__all__ = ["get_location", "SourceLocation"]


class SourceLocation(object):
    __slots__ = "line", "column"

    def __init__(self, line, column):
        # type: (int, int) -> None
        self.line = line
        self.column = column

    def __repr__(self):
        # type: () -> str
        return "SourceLocation(line={}, column={})".format(self.line, self.column)

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, SourceLocation)
            and self.line == other.line
            and self.column == other.column
        )


def get_location(source, position):
    # type: (Source, int) -> SourceLocation
    lines = source.body[:position].splitlines()
    if lines:
        line = len(lines)
        column = len(lines[-1]) + 1
    else:
        line = 1
        column = 1
    return SourceLocation(line, column)
