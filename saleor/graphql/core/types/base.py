from typing import Optional

from graphene.types.inputobjecttype import InputObjectType, InputObjectTypeOptions
from graphene.types.objecttype import ObjectType, ObjectTypeOptions


class BaseObjectOptions(ObjectTypeOptions):
    doc_category: Optional[str] = None


class BaseObjectType(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=(),
        possible_types=(),
        default_resolver=None,
        _meta=None,
        doc_category=None,
        **options,
    ):
        if not _meta:
            _meta = BaseObjectOptions(cls)

        _meta.doc_category = doc_category

        super(BaseObjectType, cls).__init_subclass_with_meta__(
            interfaces=interfaces,
            possible_types=possible_types,
            default_resolver=default_resolver,
            _meta=_meta,
            **options,
        )


class BaseInputObjectTypeOptions(InputObjectTypeOptions):
    doc_category: Optional[str] = None


class BaseInputObjectType(InputObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls, container=None, _meta=None, doc_category=None, **options
    ):
        if not _meta:
            _meta = BaseInputObjectTypeOptions(cls)

        _meta.doc_category = doc_category

        super(BaseInputObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, **options
        )
