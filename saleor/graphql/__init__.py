from typing import Any, NotRequired, TypedDict


class GraphQLOperationResult(TypedDict):
    data: NotRequired[dict[str, Any] | None]
    errors: NotRequired[list[dict[str, Any]] | None]
    extensions: NotRequired[dict[str, dict] | None]
