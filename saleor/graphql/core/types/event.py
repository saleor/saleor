from graphene import ObjectType
from graphene.types.objecttype import ObjectTypeOptions


class EventObjectType(ObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        dry_run_model_name=None,
        _meta=None,
        **options,
    ):
        if not _meta:
            _meta = ObjectTypeOptions(cls)

        _meta.dry_run_model_name = dry_run_model_name

        super().__init_subclass_with_meta__(_meta=_meta, **options)
