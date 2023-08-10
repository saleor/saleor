from typing import List

import graphene

from ...attribute import models as attribute_models
from ...page import models
from ...permission.enums import PagePermissions, PageTypePermissions
from ..attribute.filters import AttributeFilterInput, AttributeWhereInput
from ..attribute.types import Attribute, AttributeCountableConnection, SelectedAttribute
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.descriptions import ADDED_IN_33, DEPRECATED_IN_3X_FIELD, RICH_CONTENT
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.federation import federated_entity, resolve_federation_references
from ..core.fields import FilterConnectionField, JSONString, PermissionsField
from ..core.scalars import Date
from ..core.types import ModelObjectType, NonNullList
from ..meta.types import ObjectWithMetadata
from ..translations.fields import TranslationField
from ..translations.types import PageTranslation
from .dataloaders import (
    PageAttributesByPageTypeIdLoader,
    PagesByPageTypeIdLoader,
    PageTypeByIdLoader,
    SelectedAttributesByPageIdLoader,
)


@federated_entity("id")
class PageType(ModelObjectType[models.PageType]):
    id = graphene.GlobalID(required=True, description="ID of the page type.")
    name = graphene.String(required=True, description="Name of the page type.")
    slug = graphene.String(required=True, description="Slug of the page type.")
    attributes = NonNullList(
        Attribute, description="Page attributes of that page type."
    )
    available_attributes = FilterConnectionField(
        AttributeCountableConnection,
        filter=AttributeFilterInput(),
        where=AttributeWhereInput(),
        description="Attributes that can be assigned to the page type.",
        permissions=[
            PagePermissions.MANAGE_PAGES,
            PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        ],
    )
    has_pages = PermissionsField(
        graphene.Boolean,
        description="Whether page type has pages assigned.",
        permissions=[
            PagePermissions.MANAGE_PAGES,
            PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        ],
    )

    class Meta:
        description = (
            "Represents a type of page. It defines what attributes are available to "
            "pages of this type."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.PageType

    @staticmethod
    def get_model():
        return models.PageType

    @staticmethod
    def resolve_attributes(root: models.PageType, info: ResolveInfo):
        return PageAttributesByPageTypeIdLoader(info.context).load(root.pk)

    @staticmethod
    def resolve_available_attributes(
        root: models.PageType, info: ResolveInfo, **kwargs
    ):
        qs = attribute_models.Attribute.objects.get_unassigned_page_type_attributes(
            root.pk
        )
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(qs, info, kwargs, AttributeCountableConnection)

    @staticmethod
    def resolve_has_pages(root: models.PageType, info: ResolveInfo):
        return (
            PagesByPageTypeIdLoader(info.context)
            .load(root.pk)
            .then(lambda pages: bool(pages))
        )

    @staticmethod
    def __resolve_references(roots: List["PageType"], _info: ResolveInfo):
        return resolve_federation_references(PageType, roots, models.PageType.objects)


class PageTypeCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        node = PageType


class Page(ModelObjectType[models.Page]):
    id = graphene.GlobalID(required=True, description="ID of the page.")
    seo_title = graphene.String(description="Title of the page for SEO.")
    seo_description = graphene.String(description="Description of the page for SEO.")
    title = graphene.String(required=True, description="Title of the page.")
    content = JSONString(description="Content of the page." + RICH_CONTENT)
    publication_date = Date(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `publishedAt` field to fetch the publication date."
        ),
    )
    published_at = graphene.DateTime(
        description="The page publication date." + ADDED_IN_33
    )
    is_published = graphene.Boolean(
        required=True, description="Determines if the page is published."
    )
    slug = graphene.String(required=True, description="Slug of the page.")
    page_type = graphene.Field(
        PageType, required=True, description="Determines the type of page"
    )
    created = graphene.DateTime(
        required=True, description="Date and time at which page was created."
    )
    content_json = JSONString(
        description="Content of the page." + RICH_CONTENT,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `content` field instead.",
        required=True,
    )
    translation = TranslationField(PageTranslation, type_name="page")
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this product.",
    )

    class Meta:
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Page

    @staticmethod
    def resolve_publication_date(root: models.Page, _info: ResolveInfo):
        return root.published_at

    @staticmethod
    def resolve_created(root: models.Page, _info: ResolveInfo):
        return root.created_at

    @staticmethod
    def resolve_page_type(root: models.Page, info: ResolveInfo):
        return PageTypeByIdLoader(info.context).load(root.page_type_id)

    @staticmethod
    def resolve_content_json(root: models.Page, _info: ResolveInfo):
        content = root.content
        return content if content is not None else {}

    @staticmethod
    def resolve_attributes(root: models.Page, info: ResolveInfo):
        return SelectedAttributesByPageIdLoader(info.context).load(root.id)


class PageCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        node = Page
