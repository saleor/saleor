import copy
from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from django.db.models import Model, Q
from graphene.types.objecttype import ObjectType, ObjectTypeOptions

from ..descriptions import ADDED_IN_33, PREVIEW_FEATURE
from . import TYPES_WITH_DOUBLE_ID_AVAILABLE


class ModelObjectOptions(ObjectTypeOptions):
    model = None
    metadata_since = None


MT = TypeVar("MT", bound=Model)


class ModelObjectType(Generic[MT], ObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=(),
        possible_types=(),
        default_resolver=None,
        _meta=None,
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

            _meta.model = options.pop("model")
            _meta.metadata_since = options.pop("metadata_since", None)

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
                field.description = field.description + added_label + PREVIEW_FEATURE
                cls._meta.fields[field_name] = field
            elif metadata_since and field_name in ["private_metadata", "metadata"]:
                field = copy.deepcopy(field)
                field.description = field.description + metadata_since + PREVIEW_FEATURE
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
