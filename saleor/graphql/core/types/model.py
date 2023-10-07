import copy
from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from django.db.models import Model, Q
from graphene.types.objecttype import ObjectTypeOptions

from ..descriptions import ADDED_IN_33
from ..doc_category import DOC_CATEGORY_MAP
from . import TYPES_WITH_DOUBLE_ID_AVAILABLE
from .base import BaseObjectType


class ModelObjectOptions(ObjectTypeOptions):
    model = None
    metadata_since = None


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
            elif not issubclass(options["model"], Model):
                raise ValueError(
                    "ModelObjectType was declared with invalid 'model' option value "
                    "in it's Meta. Expected subclass of django.db.models.Model, "
                    f"received '{type(options['model'])}' type."
                )

            model = options.pop("model")
            _meta.model = model
            _meta.metadata_since = options.pop("metadata_since", None)

            doc_category_key = f"{model._meta.app_label}.{model.__name__}"
            if doc_category not in options:
                options["doc_category"] = doc_category
            if not options["doc_category"] and doc_category_key in DOC_CATEGORY_MAP:
                options["doc_category"] = DOC_CATEGORY_MAP[doc_category_key]

        super(ModelObjectType, cls).__init_subclass_with_meta__(
            interfaces=interfaces,
            possible_types=possible_types,
            default_resolver=default_resolver,
            _meta=_meta,
            **options,
        )

        if "ObjectWithMetadata" in {interface._meta.name for interface in interfaces}:
            cls.update_meta_fields_descriptions(_meta.metadata_since)

    @classmethod
    def update_meta_fields_descriptions(cls, metadata_since):
        """Set correct `ADDED_IN_X` label for meta fields.

        Default metadata label in Added in Saleor 3.3.
        """
        added_label = metadata_since or ADDED_IN_33
        for field_name, field in cls._meta.fields.items():
            if field_name in [
                "private_metafield",
                "private_metafields",
                "metafield",
                "metafields",
            ]:
                # each meta fields had reference to the same field so deepcopy
                # is required, otherwise the description is changed in each model
                # that inherits the `ObjectWithMetadata` interface
                field = copy.deepcopy(field)
                field.description = field.description + added_label
                cls._meta.fields[field_name] = field
            elif metadata_since and field_name in ["private_metadata", "metadata"]:
                field = copy.deepcopy(field)
                field.description = field.description + metadata_since
                cls._meta.fields[field_name] = field

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
    def get_model(cls) -> Type[MT]:
        return cls._meta.model
