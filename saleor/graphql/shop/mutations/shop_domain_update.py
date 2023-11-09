import graphene

from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.descriptions import DEPRECATED_IN_3X_MUTATION
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import ShopError
from ...site.dataloaders import get_site_promise
from ..types import Shop


class SiteDomainInput(graphene.InputObjectType):
    domain = graphene.String(description="Domain name for shop.")
    name = graphene.String(description="Shop site name.")

    class Meta:
        doc_category = DOC_CATEGORY_SHOP


class ShopDomainUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = SiteDomainInput(description="Fields required to update site.")

    class Meta:
        description = (
            "Updates site domain of the shop."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `PUBLIC_URL` environment variable instead."
        )
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        site = get_site_promise(info.context).get()
        domain = input.get("domain")
        name = input.get("name")
        if domain is not None:
            site.domain = domain
        if name is not None:
            site.name = name
        cls.clean_instance(info, site)
        site.save()
        return ShopDomainUpdate(shop=Shop())
