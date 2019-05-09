__all__ = ["Source"]


class Source(object):
    __slots__ = "body", "name"

    def __init__(self, body, name="GraphQL"):
        # type: (str, str) -> None
        self.body = body
        self.name = name

    def __eq__(self, other):
        return self is other or (
            isinstance(other, Source)
            and self.body == other.body
            and self.name == other.name
        )
