from graphene.relay.connection import Connection
from graphene.types.enum import Enum
from graphene.types.inputobjecttype import InputObjectType
from graphene.types.interface import Interface
from graphene.types.objecttype import ObjectType


class BaseObjectType(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=(),
        possible_types=(),
        default_resolver=None,
        _meta=None,
        doc_category=None,
        webhook_events_info=None,
        **options,
    ):
        cls.doc_category = doc_category
        cls.webhook_events_info = webhook_events_info
        super().__init_subclass_with_meta__(
            interfaces=interfaces,
            possible_types=possible_types,
            default_resolver=default_resolver,
            _meta=_meta,
            **options,
        )


class BaseInputObjectType(InputObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls, container=None, _meta=None, doc_category=None, **options
    ):
        # Capture string constraints BEFORE super() mounts the fields
        string_constraints = {}
        for attr_name in list(cls.__dict__):
            attr_value = cls.__dict__[attr_name]
            min_len = getattr(attr_value, "_limited_min_length", None)
            max_len = getattr(attr_value, "_limited_max_length", None)
            if min_len is not None or max_len is not None:
                string_constraints[attr_name] = (min_len, max_len)

        cls.doc_category = doc_category
        super().__init_subclass_with_meta__(container=container, _meta=_meta, **options)

        # Merge with parent constraints (parent already includes its ancestors)
        parent_constraints = {}
        for base in cls.__mro__[1:]:
            if hasattr(base, "_string_constraints"):
                parent_constraints.update(base._string_constraints)
                break
        parent_constraints.update(string_constraints)
        if parent_constraints:
            cls._string_constraints = parent_constraints


class BaseEnum(Enum):
    @classmethod
    def __init_subclass_with_meta__(
        cls, enum=None, _meta=None, doc_category=None, **options
    ):
        cls.doc_category = doc_category
        super().__init_subclass_with_meta__(enum=enum, _meta=_meta, **options)


class BaseConnection(Connection):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls, node=None, name=None, doc_category=None, **options
    ):
        cls.doc_category = doc_category
        super().__init_subclass_with_meta__(node=node, name=name, **options)


class BaseInterface(Interface):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, doc_category=None, **options):
        cls.doc_category = doc_category
        super().__init_subclass_with_meta__(
            _meta=_meta,
            **options,
        )
