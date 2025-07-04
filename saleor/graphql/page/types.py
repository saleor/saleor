import graphene

from ...attribute import models as attribute_models
from ...page import models
from ...permission.enums import PagePermissions, PageTypePermissions
from ..attribute.filters import (
    AttributeFilterInput,
    AttributeWhereInput,
    filter_attribute_search,
)
from ..attribute.types import Attribute, AttributeCountableConnection, SelectedAttribute
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.context import (
    ChannelContext,
    ChannelQsContext,
    get_database_connection_name,
)
from ..core.descriptions import DEPRECATED_IN_3X_INPUT, RICH_CONTENT
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.federation import federated_entity, resolve_federation_references
from ..core.fields import FilterConnectionField, JSONString, PermissionsField
from ..core.scalars import Date, DateTime
from ..core.types import ModelObjectType, NonNullList
from ..core.types.context import ChannelContextType
from ..meta.types import ObjectWithMetadata
from ..translations.fields import TranslationField
from ..translations.types import PageTranslation
from ..utils import get_user_or_app_from_context
from .dataloaders import (
    PageAttributesAllByPageTypeIdLoader,
    PageAttributesVisibleInStorefrontByPageTypeIdLoader,
    PagesByPageTypeIdLoader,
    PageTypeByIdLoader,
    SelectedAttributeAllByPageIdAttributeSlugLoader,
    SelectedAttributesAllByPageIdLoader,
    SelectedAttributesVisibleInStorefrontPageIdLoader,
    SelectedAttributeVisibleInStorefrontPageIdAttributeSlugLoader,
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
        filter=AttributeFilterInput(
            description="Filtering options for attributes. "
            f"{DEPRECATED_IN_3X_INPUT} Use `where` filter instead."
        ),
        where=AttributeWhereInput(
            description="Where filtering options for attributes."
        ),
        search=graphene.String(description="Search attributes."),
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
        def wrap_with_channel_context(attributes):
            return [ChannelContext(attribute, None) for attribute in attributes]

        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            return (
                PageAttributesAllByPageTypeIdLoader(info.context)
                .load(root.pk)
                .then(wrap_with_channel_context)
            )
        return (
            PageAttributesVisibleInStorefrontByPageTypeIdLoader(info.context)
            .load(root.pk)
            .then(wrap_with_channel_context)
        )

    @staticmethod
    def resolve_available_attributes(
        root: models.PageType, info: ResolveInfo, search=None, **kwargs
    ):
        qs = attribute_models.Attribute.objects.get_unassigned_page_type_attributes(
            root.pk
        ).using(get_database_connection_name(info.context))
        qs = filter_connection_queryset(
            qs, kwargs, info.context, allow_replica=info.context.allow_replica
        )
        if search:
            qs = filter_attribute_search(qs, None, search)
        qs = ChannelQsContext(qs=qs, channel_slug=None)
        return create_connection_slice(qs, info, kwargs, AttributeCountableConnection)

    @staticmethod
    def resolve_has_pages(root: models.PageType, info: ResolveInfo):
        return (
            PagesByPageTypeIdLoader(info.context)
            .load(root.pk)
            .then(lambda pages: bool(pages))
        )

    @staticmethod
    def __resolve_references(roots: list["PageType"], info: ResolveInfo):
        database_connection_name = get_database_connection_name(info.context)
        return resolve_federation_references(
            PageType, roots, models.PageType.objects.using(database_connection_name)
        )


class PageTypeCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        node = PageType


class Page(ChannelContextType[models.Page]):
    id = graphene.GlobalID(required=True, description="ID of the page.")
    seo_title = graphene.String(description="Title of the page for SEO.")
    seo_description = graphene.String(description="Description of the page for SEO.")
    title = graphene.String(required=True, description="Title of the page.")
    content = JSONString(description="Content of the page." + RICH_CONTENT)
    publication_date = Date(
        deprecation_reason="Use the `publishedAt` field to fetch the publication date."
    )
    published_at = DateTime(description="The page publication date.")
    is_published = graphene.Boolean(
        required=True, description="Determines if the page is published."
    )
    slug = graphene.String(required=True, description="Slug of the page.")
    page_type = graphene.Field(
        PageType, required=True, description="Determines the type of page"
    )
    created = DateTime(
        required=True, description="Date and time at which page was created."
    )
    content_json = JSONString(
        description="Content of the page." + RICH_CONTENT,
        deprecation_reason="Use the `content` field instead.",
        required=True,
    )
    translation = TranslationField(
        PageTranslation,
        type_name="page",
        resolver=ChannelContextType.resolve_translation,
    )
    attribute = graphene.Field(
        SelectedAttribute,
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description="Get a single attribute attached to page by attribute slug.",
    )
    attributes = NonNullList(
        SelectedAttribute,
        required=True,
        description="List of attributes assigned to this page.",
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Page

    @staticmethod
    def resolve_publication_date(root: ChannelContext[models.Page], _info: ResolveInfo):
        return root.node.published_at

    @staticmethod
    def resolve_created(root: ChannelContext[models.Page], _info: ResolveInfo):
        return root.node.created_at

    @staticmethod
    def resolve_page_type(root: ChannelContext[models.Page], info: ResolveInfo):
        return PageTypeByIdLoader(info.context).load(root.node.page_type_id)

    @staticmethod
    def resolve_content_json(root: ChannelContext[models.Page], _info: ResolveInfo):
        content = root.node.content
        return content if content is not None else {}

    @staticmethod
    def resolve_attributes(root: ChannelContext[models.Page], info: ResolveInfo):
        page = root.node

        def wrap_with_channel_context(
            attributes: list[dict[str, list]] | None,
        ) -> list[SelectedAttribute] | None:
            if attributes is None:
                return None
            return [
                SelectedAttribute(
                    attribute=ChannelContext(attribute["attribute"], root.channel_slug),
                    values=[
                        ChannelContext(value, root.channel_slug)
                        for value in attribute["values"]
                    ],
                )
                for attribute in attributes
            ]

        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            return (
                SelectedAttributesAllByPageIdLoader(info.context)
                .load(page.id)
                .then(wrap_with_channel_context)
            )
        return (
            SelectedAttributesVisibleInStorefrontPageIdLoader(info.context)
            .load(page.id)
            .then(wrap_with_channel_context)
        )

    @staticmethod
    def resolve_attribute(
        root: ChannelContext[models.Page], info: ResolveInfo, slug: str
    ):
        page = root.node

        def wrap_with_channel_context(
            attribute_data: dict[str, dict | list[dict]] | None,
        ) -> SelectedAttribute | None:
            if attribute_data is None:
                return None
            return SelectedAttribute(
                attribute=ChannelContext(
                    attribute_data["attribute"], root.channel_slug
                ),
                values=[
                    ChannelContext(value, root.channel_slug)
                    for value in attribute_data["values"]
                ],
            )

        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            return (
                SelectedAttributeAllByPageIdAttributeSlugLoader(info.context)
                .load((page.id, slug))
                .then(wrap_with_channel_context)
            )
        return (
            SelectedAttributeVisibleInStorefrontPageIdAttributeSlugLoader(info.context)
            .load((page.id, slug))
            .then(wrap_with_channel_context)
        )


class PageCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        node = Page
