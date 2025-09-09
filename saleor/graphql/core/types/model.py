from typing import Generic, TypeVar
from uuid import UUID

import graphene
from django.db.models import Model, Q
from graphene.types.objecttype import ObjectTypeOptions

from . import TYPES_WITH_DOUBLE_ID_AVAILABLE


class ModelObjectOptions(ObjectTypeOptions):
    model = None


MT = TypeVar("MT", bound=Model)


class ModelObjectType(Generic[MT], graphene.ObjectType):
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
            if not issubclass(options["model"], Model):
                raise ValueError(
                    "ModelObjectType was declared with invalid 'model' option value "
                    "in it's Meta. Expected subclass of django.db.models.Model, "
                    f"received '{type(options['model'])}' type."
                )

            model = options.pop("model")
            _meta.model = model

        super().__init_subclass_with_meta__(
            interfaces=interfaces,
            possible_types=possible_types,
            default_resolver=default_resolver,
            _meta=_meta,
            **options,
        )

    @classmethod
    def get_node(cls, _, id) -> MT | None:
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
