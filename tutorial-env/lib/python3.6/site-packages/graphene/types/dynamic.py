import inspect
from functools import partial

from .mountedtype import MountedType


class Dynamic(MountedType):
    """
    A Dynamic Type let us get the type in runtime when we generate
    the schema. So we can have lazy fields.
    """

    def __init__(self, type, with_schema=False, _creation_counter=None):
        super(Dynamic, self).__init__(_creation_counter=_creation_counter)
        assert inspect.isfunction(type) or isinstance(type, partial)
        self.type = type
        self.with_schema = with_schema

    def get_type(self, schema=None):
        if schema and self.with_schema:
            return self.type(schema=schema)
        return self.type()
