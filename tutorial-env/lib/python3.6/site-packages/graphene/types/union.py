from .base import BaseOptions, BaseType
from .unmountedtype import UnmountedType

# For static type checking with Mypy
MYPY = False
if MYPY:
    from .objecttype import ObjectType  # NOQA
    from typing import Iterable, Type  # NOQA


class UnionOptions(BaseOptions):
    types = ()  # type: Iterable[Type[ObjectType]]


class Union(UnmountedType, BaseType):
    """
    Union Type Definition

    When a field can return one of a heterogeneous set of types, a Union type
    is used to describe what types are possible as well as providing a function
    to determine which type is actually used when the field is resolved.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, types=None, **options):
        assert (
            isinstance(types, (list, tuple)) and len(types) > 0
        ), "Must provide types for Union {name}.".format(name=cls.__name__)

        _meta = UnionOptions(cls)
        _meta.types = types
        super(Union, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def get_type(cls):
        """
        This function is called when the unmounted type (Union instance)
        is mounted (as a Field, InputField or Argument)
        """
        return cls

    @classmethod
    def resolve_type(cls, instance, info):
        from .objecttype import ObjectType  # NOQA

        if isinstance(instance, ObjectType):
            return type(instance)
