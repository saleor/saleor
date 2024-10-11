from typing import Generic, Optional, TypeVar
from uuid import UUID

from django.db.models import Model, Q
from graphene.types.objecttype import ObjectTypeOptions

from ..doc_category import DOC_CATEGORY_MAP
from . import TYPES_WITH_DOUBLE_ID_AVAILABLE
from .base import BaseObjectType


class ModelObjectOptions(ObjectTypeOptions):
    model = None


MT = TypeVar("MT", bound=Model)


class ModelObjectType(Generic[MT], BaseObjectType):
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
            _meta = ModelObjectOptions(cls)

        if not getattr(_meta, "model", None):
            if not options.get("model"):
                raise ValueError(
                    "ModelObjectType was declared without 'model' option in it's Meta."
                )
            if not issubclass(options["model"], Model):
                raise ValueError(
                    "ModelObjectType was declared with invalid 'model' option value "
                    "in it's Meta. Expected subclass of django.db.models.Model, "
                    f"received '{type(options['model'])}' type."
                )

            model = options.pop("model")
            _meta.model = model

            doc_category_key = f"{model._meta.app_label}.{model.__name__}"
            if doc_category not in options:
                options["doc_category"] = doc_category
            if not options["doc_category"] and doc_category_key in DOC_CATEGORY_MAP:
                options["doc_category"] = DOC_CATEGORY_MAP[doc_category_key]

        super().__init_subclass_with_meta__(
            interfaces=interfaces,
            possible_types=possible_types,
            default_resolver=default_resolver,
            _meta=_meta,
            **options,
        )

    @classmethod
    def get_node(cls, _, id) -> Optional[MT]:
        model = cls._meta.model
        type_name = cls._meta.name
        lookup = Q(pk=id)
        if id is not None and type_name in TYPES_WITH_DOUBLE_ID_AVAILABLE:
            # This is temporary solution that allows fetching orders with use of
            # new (uuid type) and old (int type) id
            try:
                UUID(str(id))
            except ValueError:
                lookup = (
                    Q(number=id) & Q(use_old_id=True)
                    if type_name == "Order"
                    else Q(old_id=id) & Q(old_id__isnull=False)
                )
        try:
            return model.objects.get(lookup)
        except model.DoesNotExist:
            return None

    @classmethod
    def get_model(cls) -> type[MT]:
        return cls._meta.model
