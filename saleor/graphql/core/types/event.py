from graphene import ObjectType
from graphene.types.objecttype import ObjectTypeOptions


class SubscriptionObjectType(ObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        root_type=None,
        enable_dry_run=False,
        _meta=None,
        **options,
    ):
        if not _meta:
            _meta = ObjectTypeOptions(cls)

        _meta.root_type = root_type
        _meta.enable_dry_run = enable_dry_run

        super().__init_subclass_with_meta__(_meta=_meta, **options)
