import graphene

from ...attribute import models
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.context import ChannelContext, ChannelQsContext
from ..core.descriptions import DEPRECATED_IN_3X_INPUT
from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.fields import BaseField, FilterConnectionField
from ..core.utils.resolvers import resolve_by_global_id_slug_or_ext_ref
from ..translations.mutations import (
    AttributeBulkTranslate,
    AttributeTranslate,
    AttributeValueBulkTranslate,
    AttributeValueTranslate,
)
from .bulk_mutations import AttributeBulkDelete, AttributeValueBulkDelete
from .filters import AttributeFilterInput, AttributeWhereInput, filter_attribute_search
from .mutations import (
    AttributeBulkCreate,
    AttributeBulkUpdate,
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
        filter=AttributeFilterInput(
            description=(
                f"Filtering options for attributes. {DEPRECATED_IN_3X_INPUT} "
                "Use `where` filter instead."
            )
        ),
        where=AttributeWhereInput(
            description="Where filtering options for attributes."
        ),
        search=graphene.String(description="Search attributes."),
        sort_by=AttributeSortingInput(description="Sorting options for attributes."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        doc_category=DOC_CATEGORY_ATTRIBUTES,
    )
    attribute = BaseField(
        Attribute,
        id=graphene.Argument(graphene.ID, description="ID of the attribute."),
        slug=graphene.Argument(graphene.String, description="Slug of the attribute."),
        external_reference=graphene.Argument(
            graphene.String, description="External ID of the attribute."
        ),
        description="Look up an attribute by ID, slug or external reference.",
        doc_category=DOC_CATEGORY_ATTRIBUTES,
    )

    def resolve_attributes(self, info: ResolveInfo, *, search=None, **kwargs):
        qs = resolve_attributes(info)
        qs = filter_connection_queryset(
            qs, kwargs, info.context, allow_replica=info.context.allow_replica
        )
        if search:
            qs = filter_attribute_search(qs, None, search)
        qs = ChannelQsContext(qs=qs, channel_slug=None)
        return create_connection_slice(qs, info, kwargs, AttributeCountableConnection)

    def resolve_attribute(
        self, info: ResolveInfo, *, id=None, slug=None, external_reference=None
    ):
        attribute = resolve_by_global_id_slug_or_ext_ref(
            info, models.Attribute, id, slug, external_reference
        )
        if attribute:
            return ChannelContext(node=attribute, channel_slug=None)
        return None


class AttributeMutations(graphene.ObjectType):
    # attribute mutations
    attribute_create = AttributeCreate.Field()
    attribute_delete = AttributeDelete.Field()
    attribute_update = AttributeUpdate.Field()
    attribute_bulk_create = AttributeBulkCreate.Field()
    attribute_bulk_update = AttributeBulkUpdate.Field()
    attribute_translate = AttributeTranslate.Field()
    attribute_bulk_translate = AttributeBulkTranslate.Field()
    attribute_bulk_delete = AttributeBulkDelete.Field()
    attribute_value_bulk_delete = AttributeValueBulkDelete.Field()

    # attribute value mutations
    attribute_value_create = AttributeValueCreate.Field()
    attribute_value_delete = AttributeValueDelete.Field()
    attribute_value_update = AttributeValueUpdate.Field()
    attribute_value_bulk_translate = AttributeValueBulkTranslate.Field()
    attribute_value_translate = AttributeValueTranslate.Field()
    attribute_reorder_values = AttributeReorderValues.Field()
