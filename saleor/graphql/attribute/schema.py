import graphene

from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.fields import FilterConnectionField
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
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
from .resolvers import (
    resolve_attribute_by_ext_ref,
    resolve_attribute_by_id,
    resolve_attribute_by_slug,
    resolve_attributes,
)
from .sorters import AttributeSortingInput
from .types import Attribute, AttributeCountableConnection


class AttributeQueries(graphene.ObjectType):
    attributes = FilterConnectionField(
        AttributeCountableConnection,
        description="List of the shop's attributes.",
        filter=AttributeFilterInput(description="Filtering options for attributes."),
        sort_by=AttributeSortingInput(description="Sorting options for attributes."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    attribute = graphene.Field(
        Attribute,
        id=graphene.Argument(graphene.ID, description="ID of the attribute."),
        slug=graphene.Argument(graphene.String, description="Slug of the attribute."),
        external_reference=graphene.Argument(
            graphene.String, description="External ID of the attribute."
        ),
        description="Look up an attribute by ID, slug or external reference.",
    )

    def resolve_attributes(self, info, **kwargs):
        qs = resolve_attributes(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(qs, info, kwargs, AttributeCountableConnection)

    def resolve_attribute(self, _info, *, id=None, slug=None, external_reference=None):
        validate_one_of_args_is_in_query(
            "id", id, "slug", slug, "external_reference", external_reference
        )
        if id:
            _, id = from_global_id_or_error(id, Attribute)
            return resolve_attribute_by_id(id)
        if slug:
            return resolve_attribute_by_slug(slug=slug)
        return resolve_attribute_by_ext_ref(external_reference)


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
