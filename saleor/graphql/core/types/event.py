from graphene.types.objecttype import ObjectTypeOptions

from ..doc_category import DOC_CATEGORY_MAP
from ..types import BaseObjectType

# Rewrite original map to use model to category mapping, with the app name skipped,
# so that it can be used with root_type from SubscriptionObjectType.
DOC_CATEGORY_MODEL_MAP = {
    key.split(".")[1]: value for key, value in DOC_CATEGORY_MAP.items()
}


class SubscriptionObjectType(BaseObjectType):
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

        if (
            "doc_category" not in options
            and root_type
            and root_type in DOC_CATEGORY_MODEL_MAP
        ):
            options["doc_category"] = DOC_CATEGORY_MODEL_MAP[root_type]

        if "doc_category" not in options and root_type is None:
            raise NotImplementedError(
                f"SubscriptionObjectType {cls.__name__} must have a root_type defined."
            )

        super().__init_subclass_with_meta__(_meta=_meta, **options)
