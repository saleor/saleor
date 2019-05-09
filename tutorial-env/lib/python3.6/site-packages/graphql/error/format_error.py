from six import text_type

from .base import GraphQLError

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Dict, Union


def format_error(error):
    # type: (Exception) -> Dict[str, Any]
    formatted_error = {"message": text_type(error)}  # type: Dict[str, Any]
    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error["locations"] = [
                {"line": loc.line, "column": loc.column} for loc in error.locations
            ]
        if error.path is not None:
            formatted_error["path"] = error.path

    return formatted_error
