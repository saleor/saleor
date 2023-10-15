import graphene

from ....account import models as account_models
from ....graphql.account.mixins import AddressMetadataMixin
from ....permission.enums import SitePermissions
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import ShopError
from ...site.dataloaders import get_site_promise
from ..types import Shop


class ShopAddressUpdate(AddressMetadataMixin, BaseMutation, I18nMixin):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = AddressInput(description="Fields required to update shop address.")

    class Meta:
        description = (
            "Update the shop's address. If the `null` value is passed, the currently "
            "selected address will be deleted."
        )
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        data = data.get("input")

        if data:
            if not site.settings.company_address:
                company_address = account_models.Address()
            else:
                company_address = site.settings.company_address
            company_address = cls.validate_address(
                data, instance=company_address, info=info
            )
            company_address.save()
            site.settings.company_address = company_address
            site.settings.save(update_fields=["company_address"])
        else:
            if site.settings.company_address:
                site.settings.company_address.delete()
        return ShopAddressUpdate(shop=Shop())
