from collections import OrderedDict

from .base import BaseOptions, BaseType
from .field import Field
from .interface import Interface
from .utils import yank_fields_from_attrs

# For static type checking with Mypy
MYPY = False
if MYPY:
    from typing import Dict, Iterable, Type  # NOQA


class ObjectTypeOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]
    interfaces = ()  # type: Iterable[Type[Interface]]


class ObjectType(BaseType):
    """
    Object Type Definition

    Almost all of the GraphQL types you define will be object types. Object types
    have a name, but most importantly describe their fields.
    """

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=(),
        possible_types=(),
        default_resolver=None,
        _meta=None,
        **options
    ):
        if not _meta:
            _meta = ObjectTypeOptions(cls)

        fields = OrderedDict()

        for interface in interfaces:
            assert issubclass(interface, Interface), (
                'All interfaces of {} must be a subclass of Interface. Received "{}".'
            ).format(cls.__name__, interface)
            fields.update(interface._meta.fields)

        for base in reversed(cls.__mro__):
            fields.update(yank_fields_from_attrs(base.__dict__, _as=Field))

        assert not (possible_types and cls.is_type_of), (
            "{name}.Meta.possible_types will cause type collision with {name}.is_type_of. "
            "Please use one or other."
        ).format(name=cls.__name__)

        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields

        _meta.interfaces = interfaces
        _meta.possible_types = possible_types
        _meta.default_resolver = default_resolver

        super(ObjectType, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    is_type_of = None

    def __init__(self, *args, **kwargs):
        # ObjectType acting as container
        args_len = len(args)
        fields = self._meta.fields.items()
        if args_len > len(fields):
            # Daft, but matches old exception sans the err msg.
            raise IndexError("Number of args exceeds number of fields")
        fields_iter = iter(fields)

        if not kwargs:
            for val, (name, field) in zip(args, fields_iter):
                setattr(self, name, val)
        else:
            for val, (name, field) in zip(args, fields_iter):
                setattr(self, name, val)
                kwargs.pop(name, None)

        for name, field in fields_iter:
            try:
                val = kwargs.pop(
                    name, field.default_value if isinstance(field, Field) else None
                )
                setattr(self, name, val)
            except KeyError:
                pass

        if kwargs:
            for prop in list(kwargs):
                try:
                    if isinstance(
                        getattr(self.__class__, prop), property
                    ) or prop.startswith("_"):
                        setattr(self, prop, kwargs.pop(prop))
                except AttributeError:
                    pass
            if kwargs:
                raise TypeError(
                    "'{}' is an invalid keyword argument for {}".format(
                        list(kwargs)[0], self.__class__.__name__
                    )
                )
