import graphene
from graphene_federation import key

from ...core.permissions import PagePermissions
from ...page import models
from ...product import models as product_models
from ..core.connection import CountableDjangoObjectType
from ..meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ..meta.types import ObjectWithMetadata
from ..core.fields import FilterInputConnectionField
from ..decorators import permission_required
from ..product.dataloaders.attributes import PageAttributesByPageTypeIdLoader
from ..product.filters import AttributeFilterInput
from ..product.types import Attribute
from ..translations.fields import TranslationField
from ..translations.types import PageTranslation


class Page(CountableDjangoObjectType):
    translation = TranslationField(PageTranslation, type_name="page")

    class Meta:
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        only_fields = [
            "content",
            "content_json",
            "created",
            "id",
            "is_published",
            "publication_date",
            "seo_description",
            "seo_title",
            "slug",
            "title",
        ]
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Page

    @staticmethod
    def resolve_meta(root: models.Page, info):
        return resolve_meta(root, info)

    @staticmethod
    def resolve_private_meta(root: models.Page, _info):
        return resolve_private_meta(root, _info)


@key(fields="id")
class PageType(CountableDjangoObjectType):
    attributes = graphene.List(
        Attribute, description="Page type attribute of that page type."
    )
    available_attributes = FilterInputConnectionField(
        Attribute,
        filter=AttributeFilterInput(),
        description="Attributes that can be assigned to the page type.",
    )

    class Meta:
        description = (
            "Represents a type of page. It defines what attributes are available to "
            "pages of this type."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.PageType
        only_fields = ["id", "name", "slug"]

    @staticmethod
    def resolve_attributes(root: models.PageType, info):
        return PageAttributesByPageTypeIdLoader(info.context).load(root.pk)

    @staticmethod
    @permission_required(PagePermissions.MANAGE_PAGES)
    def resolve_available_attributes(root: models.PageType, info, **kwargs):
        return product_models.Attribute.objects.get_unassigned_page_type_attributes(
            root.pk
        )
