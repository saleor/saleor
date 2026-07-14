import graphene

from ...permission.enums import GiftcardPermissions
from ..core.descriptions import DEFAULT_DEPRECATION_REASON
from ..core.doc_category import (
    DOC_CATEGORY_GIFT_CARDS,
    DOC_CATEGORY_SHOP,
)
from ..core.fields import PermissionsField
from ..site.dataloaders import load_site_callback
from ..translations.mutations import ShopSettingsTranslate
from .mutations import (
    GiftCardSettingsUpdate,
    RefundReasonReferenceTypeClear,
    RefundSettingsUpdate,
    ReturnReasonReferenceTypeClear,
    ReturnSettingsUpdate,
    ShopAddressUpdate,
    ShopDomainUpdate,
    ShopFetchTaxRates,
    ShopSettingsUpdate,
    StaffNotificationRecipientCreate,
    StaffNotificationRecipientDelete,
    StaffNotificationRecipientUpdate,
)
from .types import GiftCardSettings, RefundSettings, ReturnSettings, Shop


class ShopQueries(graphene.ObjectType):
    shop = graphene.Field(
        Shop,
        description="Return information about the shop.",
        required=True,
    )
    gift_card_settings = PermissionsField(
        GiftCardSettings,
        description="Gift card related settings from site settings.",
        required=True,
        permissions=[GiftcardPermissions.MANAGE_GIFT_CARD],
        doc_category=DOC_CATEGORY_GIFT_CARDS,
    )
    refund_settings = PermissionsField(
        RefundSettings,
        description="Refunds related settings. Returns `RefundSettings` configuration, global for the entire shop.",
        required=True,
        permissions=[],
        doc_category=DOC_CATEGORY_SHOP,
    )
    return_settings = PermissionsField(
        ReturnSettings,
        description="Returns related settings. Returns `ReturnSettings` configuration, global for the entire shop.",
        required=True,
        permissions=[],
        doc_category=DOC_CATEGORY_SHOP,
    )

    def resolve_shop(self, _info):
        return Shop()

    @load_site_callback
    def resolve_gift_card_settings(self, _info, site):
        return site.settings

    @load_site_callback
    def resolve_refund_settings(self, _info, site):
        return site.settings

    @load_site_callback
    def resolve_return_settings(self, _info, site):
        return site.settings


class ShopMutations(graphene.ObjectType):
    staff_notification_recipient_create = StaffNotificationRecipientCreate.Field()
    staff_notification_recipient_update = StaffNotificationRecipientUpdate.Field()
    staff_notification_recipient_delete = StaffNotificationRecipientDelete.Field()

    shop_domain_update = ShopDomainUpdate.Field(
        deprecation_reason="Use `PUBLIC_URL` environment variable instead."
    )
    shop_settings_update = ShopSettingsUpdate.Field()
    shop_fetch_tax_rates = ShopFetchTaxRates.Field(
        deprecation_reason=DEFAULT_DEPRECATION_REASON
    )
    shop_settings_translate = ShopSettingsTranslate.Field()
    shop_address_update = ShopAddressUpdate.Field()

    gift_card_settings_update = GiftCardSettingsUpdate.Field()
    refund_settings_update = RefundSettingsUpdate.Field()
    refund_reason_reference_clear = RefundReasonReferenceTypeClear.Field()
    return_settings_update = ReturnSettingsUpdate.Field()
    return_reason_reference_clear = ReturnReasonReferenceTypeClear.Field()
