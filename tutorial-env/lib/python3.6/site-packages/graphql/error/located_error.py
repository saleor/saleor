import sys

from .base import GraphQLError

# Necessary for static type checking
if False:  # flake8: noqa
    from ..language.ast import Field
    from typing import List, Union

__all__ = ["GraphQLLocatedError"]


class GraphQLLocatedError(GraphQLError):
    def __init__(
        self,
        nodes,  # type: List[Field]
        original_error=None,  # type: Exception
        path=None,  # type: Union[List[Union[int, str]], List[str]]
    ):
        # type: (...) -> None
        if original_error:
            try:
                message = str(original_error)
            except UnicodeEncodeError:
                message = original_error.message.encode("utf-8")  # type: ignore
        else:
            message = "An unknown error occurred."

        stack = original_error and getattr(original_error, "stack", None)
        if not stack:
            stack = sys.exc_info()[2]

        super(GraphQLLocatedError, self).__init__(
            message=message, nodes=nodes, stack=stack, path=path
        )
        self.original_error = original_error
