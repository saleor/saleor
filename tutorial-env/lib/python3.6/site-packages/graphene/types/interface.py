from collections import OrderedDict

from .base import BaseOptions, BaseType
from .field import Field
from .utils import yank_fields_from_attrs

# For static type checking with Mypy
MYPY = False
if MYPY:
    from typing import Dict  # NOQA


class InterfaceOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]


class Interface(BaseType):
    """
    Interface Type Definition

    When a field can return one of a heterogeneous set of types, a Interface type
    is used to describe what types are possible, what fields are in common across
    all types, as well as a function to determine which type is actually used
    when the field is resolved.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, **options):
        if not _meta:
            _meta = InterfaceOptions(cls)

        fields = OrderedDict()
        for base in reversed(cls.__mro__):
            fields.update(yank_fields_from_attrs(base.__dict__, _as=Field))

        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields

        super(Interface, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def resolve_type(cls, instance, info):
        from .objecttype import ObjectType

        if isinstance(instance, ObjectType):
            return type(instance)

    def __init__(self, *args, **kwargs):
        raise Exception("An Interface cannot be intitialized")
