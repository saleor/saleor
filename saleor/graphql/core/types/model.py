from uuid import UUID

from django.db.models import Model, Q
from graphene.types.objecttype import ObjectType, ObjectTypeOptions

from . import TYPES_WITH_DOUBLE_ID_AVAILABLE


class ModelObjectOptions(ObjectTypeOptions):
    model = None


class ModelObjectType(ObjectType):
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

        super(ModelObjectType, cls).__init_subclass_with_meta__(
            interfaces=interfaces,
            possible_types=possible_types,
            default_resolver=default_resolver,
            _meta=_meta,
            **options,
        )

    @classmethod
    def get_node(cls, _, id):
        model = cls._meta.model
        type_name = cls._meta.name
        try:
            if type_name in TYPES_WITH_DOUBLE_ID_AVAILABLE:
                return cls._get_node_for_types_with_double_id(id, model, type_name)
            return model.objects.get(pk=id)
        except model.DoesNotExist:
            return None

    @classmethod
    def _get_node_for_types_with_double_id(cls, id, model, type_name):
        # This is temporary method that allows fetching orders with use of
        # new (uuid type) and old (int type) id
        lookup = Q(pk=id)
        if id is not None:
            try:
                UUID(str(id))
            except ValueError:
                lookup = (
                    Q(number=id) & Q(use_old_id=True)
                    if type_name == "Order"
                    else Q(old_id=id) & Q(old_id__isnull=False)
                )
        return model.objects.get(lookup)

    @classmethod
    def get_model(cls):
        return cls._meta.model
