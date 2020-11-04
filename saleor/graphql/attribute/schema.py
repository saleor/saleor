import graphene

from ..core.fields import FilterInputConnectionField
from ..translations.mutations import AttributeTranslate, AttributeValueTranslate
from .bulk_mutations import AttributeBulkDelete, AttributeValueBulkDelete
from .filters import AttributeFilterInput
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
from .resolvers import resolve_attributes
from .sorters import AttributeSortingInput
from .types import Attribute


class AttributeQueries(graphene.ObjectType):
    attributes = FilterInputConnectionField(
        Attribute,
        description="List of the shop's attributes.",
        filter=AttributeFilterInput(description="Filtering options for attributes."),
        sort_by=AttributeSortingInput(description="Sorting options for attributes."),
    )
    attribute = graphene.Field(
        Attribute,
        id=graphene.Argument(
            graphene.ID, description="ID of the attribute.", required=True
        ),
        description="Look up an attribute by ID.",
    )

    def resolve_attributes(self, info, **kwargs):
        return resolve_attributes(info, **kwargs)

    def resolve_attribute(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Attribute)


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
