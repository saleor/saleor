from graphene.relay.connection import Connection
from graphene.types.enum import Enum
from graphene.types.inputobjecttype import InputObjectType
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
        cls.doc_category = doc_category
        super().__init_subclass_with_meta__(container=container, _meta=_meta, **options)


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
