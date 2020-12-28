import graphene

from ..core.fields import FilterInputConnectionField
from ..translations.mutations import AttributeTranslate, AttributeValueTranslate
from .bulk_mutations import AttributeBulkDelete, AttributeValueBulkDelete
from .filters import AttributeFilterInput
from .mutations import (
    AttributeCreate,
    AttributeDelete,
    AttributeReorderValues,
    AttributeUpdate,
    AttributeValueCreate,
    AttributeValueDelete,
    AttributeValueUpdate,
)
from .resolvers import resolve_attribute_by_slug, resolve_attributes
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
        id=graphene.Argument(graphene.ID, description="ID of the attribute."),
        slug=graphene.Argument(graphene.String, description="Slug of the attribute."),
        description="Look up an attribute by ID.",
    )

    def resolve_attributes(self, info, **kwargs):
        return resolve_attributes(info, **kwargs)

    def resolve_attribute(self, info, id=None, slug=None):
        if id:
            return graphene.Node.get_node_from_global_id(info, id, Attribute)
        return resolve_attribute_by_slug(slug=slug)


class AttributeMutations(graphene.ObjectType):
    # attribute mutations
    attribute_create = AttributeCreate.Field()
    attribute_delete = AttributeDelete.Field()
    attribute_update = AttributeUpdate.Field()
    attribute_translate = AttributeTranslate.Field()
    attribute_bulk_delete = AttributeBulkDelete.Field()
    attribute_value_bulk_delete = AttributeValueBulkDelete.Field()

    # attribute value mutations
    attribute_value_create = AttributeValueCreate.Field()
    attribute_value_delete = AttributeValueDelete.Field()
    attribute_value_update = AttributeValueUpdate.Field()
    attribute_value_translate = AttributeValueTranslate.Field()
    attribute_reorder_values = AttributeReorderValues.Field()
