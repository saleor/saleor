import graphene
from graphene.types.objecttype import ObjectTypeOptions

from ..doc_category import DOC_CATEGORY_MAP

# Rewrite original map to use model to category mapping, with the app name skipped,
# so that it can be used with root_type from SubscriptionObjectType.
DOC_CATEGORY_MODEL_MAP = {
    key.split(".")[1]: value for key, value in DOC_CATEGORY_MAP.items()
}


class SubscriptionObjectType(graphene.ObjectType):
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
