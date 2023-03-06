import graphene

from ...core.permissions import GiftcardPermissions, OrderPermissions
from ..core.descriptions import DEPRECATED_IN_3X_MUTATION
from ..core.fields import PermissionsField
from ..site.dataloaders import load_site_callback
from ..translations.mutations import ShopSettingsTranslate
from .mutations import (
    GiftCardSettingsUpdate,
    OrderSettingsUpdate,
    ShopAddressUpdate,
    ShopDomainUpdate,
    ShopFetchTaxRates,
    ShopSettingsUpdate,
    StaffNotificationRecipientCreate,
    StaffNotificationRecipientDelete,
    StaffNotificationRecipientUpdate,
)
from .types import GiftCardSettings, OrderSettings, Shop


class ShopQueries(graphene.ObjectType):
    shop = graphene.Field(
        Shop,
        description="Return information about the shop.",
        required=True,
    )
    order_settings = PermissionsField(
        OrderSettings,
        description="Order related settings from site settings.",
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    gift_card_settings = PermissionsField(
        GiftCardSettings,
        description="Gift card related settings from site settings.",
        required=True,
        permissions=[GiftcardPermissions.MANAGE_GIFT_CARD],
    )

    def resolve_shop(self, _info):
        return Shop()

    @load_site_callback
    def resolve_order_settings(self, _info, site):
        return site.settings

    @load_site_callback
    def resolve_gift_card_settings(self, _info, site):
        return site.settings


class ShopMutations(graphene.ObjectType):
    staff_notification_recipient_create = StaffNotificationRecipientCreate.Field()
    staff_notification_recipient_update = StaffNotificationRecipientUpdate.Field()
    staff_notification_recipient_delete = StaffNotificationRecipientDelete.Field()

    shop_domain_update = ShopDomainUpdate.Field()
    shop_settings_update = ShopSettingsUpdate.Field()
    shop_fetch_tax_rates = ShopFetchTaxRates.Field(
        deprecation_reason=DEPRECATED_IN_3X_MUTATION
    )
    shop_settings_translate = ShopSettingsTranslate.Field()
    shop_address_update = ShopAddressUpdate.Field()

    order_settings_update = OrderSettingsUpdate.Field()
    gift_card_settings_update = GiftCardSettingsUpdate.Field()
