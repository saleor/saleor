from uuid import UUID

from django.db.models import Model, Q
from graphene.types.objecttype import ObjectType, ObjectTypeOptions


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
        try:
            if cls._meta.name == "Order":
                return cls._get_order(id, model)
            return model.objects.get(pk=id)
        except model.DoesNotExist:
            return None

    @classmethod
    def _get_order(cls, id, model):
        # This is temporary method that allows fetching orders with use of
        # new (uuid type) and old (int type) id
        lookup = Q(pk=id)
        if id is not None:
            try:
                UUID(str(id))
            except ValueError:
                lookup = Q(number=id) & Q(use_old_id=True)
        return model.objects.get(lookup)

    @classmethod
    def get_model(cls):
        return cls._meta.model
