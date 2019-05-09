import six
from ..language.location import get_location

# Necessary for static type checking
if False:  # flake8: noqa
    from ..language.source import Source
    from ..language.location import SourceLocation
    from types import TracebackType
    from typing import Optional, List, Any, Union


class GraphQLError(Exception):
    __slots__ = (
        "message",
        "nodes",
        "stack",
        "original_error",
        "_source",
        "_positions",
        "_locations",
        "path",
    )

    def __init__(
        self,
        message,  # type: str
        nodes=None,  # type: Any
        stack=None,  # type: Optional[TracebackType]
        source=None,  # type: Optional[Any]
        positions=None,  # type: Optional[Any]
        locations=None,  # type: Optional[Any]
        path=None,  # type: Union[List[Union[int, str]], List[str], None]
    ):
        # type: (...) -> None
        super(GraphQLError, self).__init__(message)
        self.message = message
        self.nodes = nodes
        self.stack = stack
        self._source = source
        self._positions = positions
        self._locations = locations
        self.path = path
        return None

    @property
    def source(self):
        # type: () -> Optional[Source]
        if self._source:
            return self._source
        if self.nodes:
            node = self.nodes[0]
            return node and node.loc and node.loc.source
        return None

    @property
    def positions(self):
        # type: () -> Optional[List[int]]
        if self._positions:
            return self._positions
        if self.nodes is not None:
            node_positions = [node.loc and node.loc.start for node in self.nodes]
            if any(node_positions):
                return node_positions
        return None

    def reraise(self):
        # type: () -> None
        if self.stack:
            six.reraise(type(self), self, self.stack)
        else:
            raise self

    @property
    def locations(self):
        # type: () -> Optional[List[SourceLocation]]
        if not self._locations:
            source = self.source
            if self.positions and source:
                self._locations = [get_location(source, pos) for pos in self.positions]
        return self._locations
