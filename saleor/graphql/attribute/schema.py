import graphene

from ...attribute import models
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_310, ADDED_IN_311, PREVIEW_FEATURE
from ..core.fields import FilterConnectionField
from ..core.utils.resolvers import resolve_by_global_id_slug_or_ext_ref
from ..translations.mutations import AttributeTranslate, AttributeValueTranslate
from .bulk_mutations import AttributeBulkDelete, AttributeValueBulkDelete
from .filters import AttributeFilterInput, AttributeWhereInput, filter_attribute_search
from .mutations import (
    AttributeCreate,
    AttributeDelete,
    AttributeReorderValues,
    AttributeUpdate,
    AttributeValueCreate,
    AttributeValueDelete,
    AttributeValueUpdate,
)
from .resolvers import resolve_attributes
from .sorters import AttributeSortingInput
from .types import Attribute, AttributeCountableConnection


class AttributeQueries(graphene.ObjectType):
    attributes = FilterConnectionField(
        AttributeCountableConnection,
        description="List of the shop's attributes.",
        filter=AttributeFilterInput(description="Filtering options for attributes."),
        where=AttributeWhereInput(
            description="Filtering options for attributes."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        ),
        search=graphene.String(
            description="Search attributes." + ADDED_IN_311 + PREVIEW_FEATURE
        ),
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
            graphene.String, description=f"External ID of the attribute. {ADDED_IN_310}"
        ),
        description="Look up an attribute by ID, slug or external reference.",
    )

    def resolve_attributes(self, info: ResolveInfo, *, search=None, **kwargs):
        qs = resolve_attributes(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        if search:
            qs = filter_attribute_search(qs, None, search)
        return create_connection_slice(qs, info, kwargs, AttributeCountableConnection)

    def resolve_attribute(
        self, _info: ResolveInfo, *, id=None, slug=None, external_reference=None
    ):
        return resolve_by_global_id_slug_or_ext_ref(
            models.Attribute, id, slug, external_reference
        )


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
