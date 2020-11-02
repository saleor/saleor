import graphene

from ..translations.mutations import AttributeTranslate, AttributeValueTranslate
from .bulk_mutations import AttributeBulkDelete, AttributeValueBulkDelete
from .mutations import (
    AttributeClearMeta,
    AttributeClearPrivateMeta,
    AttributeCreate,
    AttributeDelete,
    AttributeReorderValues,
    AttributeUpdate,
    AttributeUpdateMeta,
    AttributeUpdatePrivateMeta,
    AttributeValueCreate,
    AttributeValueDelete,
    AttributeValueUpdate,
)


class AttributeMutations(graphene.ObjectType):
    # attribute mutations
    attribute_create = AttributeCreate.Field()
    attribute_delete = AttributeDelete.Field()
    attribute_update = AttributeUpdate.Field()
    attribute_translate = AttributeTranslate.Field()
    attribute_bulk_delete = AttributeBulkDelete.Field()
    attribute_value_bulk_delete = AttributeValueBulkDelete.Field()

    # meta mutations
    attribute_update_metadata = AttributeUpdateMeta.Field(
        deprecation_reason=(
            "Use the `updateMetadata` mutation instead. This field will be removed "
            "after 2020-07-31."
        )
    )
    attribute_clear_metadata = AttributeClearMeta.Field(
        deprecation_reason=(
            "Use the `deleteMetadata` mutation instead. This field will be removed "
            "after 2020-07-31."
        )
    )
    attribute_update_private_metadata = AttributeUpdatePrivateMeta.Field(
        deprecation_reason=(
            "Use the `updatePrivateMetadata` mutation instead. This field will be "
            "removed after 2020-07-31."
        )
    )
    attribute_clear_private_metadata = AttributeClearPrivateMeta.Field(
        deprecation_reason=(
            "Use the `deletePrivateMetadata` mutation instead. This field will be "
            "removed after 2020-07-31."
        )
    )

    # attribute value mutations
    attribute_value_create = AttributeValueCreate.Field()
    attribute_value_delete = AttributeValueDelete.Field()
    attribute_value_update = AttributeValueUpdate.Field()
    attribute_value_translate = AttributeValueTranslate.Field()
    attribute_reorder_values = AttributeReorderValues.Field()
