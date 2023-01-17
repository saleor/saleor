import graphene
from django.core.exceptions import ValidationError

from ...account import models as account_models
from ...core.error_codes import ShopErrorCode
from ...core.permissions import GiftcardPermissions, OrderPermissions, SitePermissions
from ...core.utils.url import validate_storefront_url
from ...site import GiftCardSettingsExpiryType
from ...site.error_codes import GiftCardSettingsErrorCode
from ...site.models import DEFAULT_LIMIT_QUANTITY_PER_CHECKOUT
from ..account.i18n import I18nMixin
from ..account.types import AddressInput, StaffNotificationRecipient
from ..core import ResolveInfo
from ..core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_INPUT, PREVIEW_FEATURE
from ..core.enums import WeightUnitsEnum
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import (
    GiftCardSettingsError,
    OrderSettingsError,
    ShopError,
    TimePeriodInputType,
)
from ..site.dataloaders import get_site_promise
from .enums import GiftCardSettingsExpiryTypeEnum
from .types import GiftCardSettings, OrderSettings, Shop


class ShopSettingsInput(graphene.InputObjectType):
    header_text = graphene.String(description="Header text.")
    description = graphene.String(description="SEO description.")
    track_inventory_by_default = graphene.Boolean(
        description="Enable inventory tracking."
    )
    default_weight_unit = WeightUnitsEnum(description="Default weight unit.")
    automatic_fulfillment_digital_products = graphene.Boolean(
        description="Enable automatic fulfillment for all digital products."
    )
    fulfillment_auto_approve = graphene.Boolean(
        description="Enable automatic approval of all new fulfillments." + ADDED_IN_31
    )
    fulfillment_allow_unpaid = graphene.Boolean(
        description=(
            "Enable ability to approve fulfillments which are unpaid." + ADDED_IN_31
        )
    )
    default_digital_max_downloads = graphene.Int(
        description="Default number of max downloads per digital content URL."
    )
    default_digital_url_valid_days = graphene.Int(
        description="Default number of days which digital content URL will be valid."
    )
    default_mail_sender_name = graphene.String(
        description="Default email sender's name."
    )
    default_mail_sender_address = graphene.String(
        description="Default email sender's address."
    )
    customer_set_password_url = graphene.String(
        description="URL of a view where customers can set their password."
    )
    reserve_stock_duration_anonymous_user = graphene.Int(
        description=(
            "Default number of minutes stock will be reserved for "
            "anonymous checkout. Enter 0 or null to disable." + ADDED_IN_31
        )
    )
    reserve_stock_duration_authenticated_user = graphene.Int(
        description=(
            "Default number of minutes stock will be reserved for "
            "authenticated checkout. Enter 0 or null to disable." + ADDED_IN_31
        )
    )
    limit_quantity_per_checkout = graphene.Int(
        description=(
            "Default number of maximum line quantity "
            "in single checkout. Minimum possible value is 1, default "
            f"value is {DEFAULT_LIMIT_QUANTITY_PER_CHECKOUT}."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        )
    )

    # deprecated
    include_taxes_in_prices = graphene.Boolean(
        description=(
            f"Include taxes in prices. {DEPRECATED_IN_3X_INPUT} Use "
            "`taxConfigurationUpdate` mutation to configure this setting per channel "
            "or country."
        )
    )
    display_gross_prices = graphene.Boolean(
        description=(
            f"Display prices with tax in store. {DEPRECATED_IN_3X_INPUT} Use "
            "`taxConfigurationUpdate` mutation to configure this setting per channel "
            "or country."
        )
    )
    charge_taxes_on_shipping = graphene.Boolean(
        description=(
            f"Charge taxes on shipping. {DEPRECATED_IN_3X_INPUT} To enable taxes for "
            "a shipping method, assign a tax class to the shipping method with "
            "`shippingPriceCreate` or `shippingPriceUpdate` mutations."
        ),
    )


class SiteDomainInput(graphene.InputObjectType):
    domain = graphene.String(description="Domain name for shop.")
    name = graphene.String(description="Shop site name.")


class ShopSettingsUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = ShopSettingsInput(
            description="Fields required to update shop settings.", required=True
        )

    class Meta:
        description = "Updates shop settings."
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def clean_input(cls, _info, _instance, data):
        if data.get("customer_set_password_url"):
            try:
                validate_storefront_url(data["customer_set_password_url"])
            except ValidationError as error:
                raise ValidationError(
                    {"customer_set_password_url": error},
                    code=ShopErrorCode.INVALID.value,
                )

        if "reserve_stock_duration_anonymous_user" in data:
            new_value = data["reserve_stock_duration_anonymous_user"]
            if not new_value or new_value < 1:
                data["reserve_stock_duration_anonymous_user"] = None
        if "reserve_stock_duration_authenticated_user" in data:
            new_value = data["reserve_stock_duration_authenticated_user"]
            if not new_value or new_value < 1:
                data["reserve_stock_duration_authenticated_user"] = None
        if "limit_quantity_per_checkout" in data:
            new_value = data["limit_quantity_per_checkout"]
            if new_value is not None and new_value < 1:
                raise ValidationError(
                    {
                        "limit_quantity_per_checkout": ValidationError(
                            "Quantity limit cannot be lower than 1.",
                            code=ShopErrorCode.INVALID.value,
                        )
                    }
                )
            if not new_value:
                data["limit_quantity_per_checkout"] = None

        return data

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        for field_name, desired_value in cleaned_data.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)
        return instance

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        instance = site.settings
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        instance.save()
        return ShopSettingsUpdate(shop=Shop())


class ShopAddressUpdate(BaseMutation, I18nMixin):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = AddressInput(description="Fields required to update shop address.")

    class Meta:
        description = (
            "Update the shop's address. If the `null` value is passed, the currently "
            "selected address will be deleted."
        )
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


class ShopDomainUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = SiteDomainInput(description="Fields required to update site.")

    class Meta:
        description = "Updates site domain of the shop."
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


class ShopFetchTaxRates(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Meta:
        description = "Fetch tax rates."
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /):
        # This mutation is deprecated and will be removed in Saleor 4.0.
        return ShopFetchTaxRates(shop=Shop())


class StaffNotificationRecipientInput(graphene.InputObjectType):
    user = graphene.ID(
        required=False,
        description="The ID of the user subscribed to email notifications..",
    )
    email = graphene.String(
        required=False,
        description="Email address of a user subscribed to email notifications.",
    )
    active = graphene.Boolean(
        required=False, description="Determines if a notification active."
    )


class StaffNotificationRecipientCreate(ModelMutation):
    class Arguments:
        input = StaffNotificationRecipientInput(
            required=True,
            description="Fields required to create a staff notification recipient.",
        )

    class Meta:
        description = "Creates a new staff notification recipient."
        model = account_models.StaffNotificationRecipient
        object_type = StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cls.validate_input(instance, cleaned_input)
        email = cleaned_input.pop("email", None)
        if email:
            staff_user = account_models.User.objects.filter(email=email).first()
            if staff_user:
                cleaned_input["user"] = staff_user
            else:
                cleaned_input["staff_email"] = email
        return cleaned_input

    @staticmethod
    def validate_input(instance, cleaned_input):
        email = cleaned_input.get("email")
        user = cleaned_input.get("user")
        if not email and not user:
            if instance.id and "user" in cleaned_input or "email" in cleaned_input:
                raise ValidationError(
                    {
                        "staff_notification": ValidationError(
                            "User and email cannot be set empty",
                            code=ShopErrorCode.INVALID.value,
                        )
                    }
                )
            if not instance.id:
                raise ValidationError(
                    {
                        "staff_notification": ValidationError(
                            "User or email is required",
                            code=ShopErrorCode.REQUIRED.value,
                        )
                    }
                )
        if user and not user.is_staff:
            raise ValidationError(
                {
                    "user": ValidationError(
                        "User has to be staff user", code=ShopErrorCode.INVALID.value
                    )
                }
            )


class StaffNotificationRecipientUpdate(StaffNotificationRecipientCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a staff notification recipient to update."
        )
        input = StaffNotificationRecipientInput(
            required=True,
            description="Fields required to update a staff notification recipient.",
        )

    class Meta:
        description = "Updates a staff notification recipient."
        model = account_models.StaffNotificationRecipient
        object_type = StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"


class StaffNotificationRecipientDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a staff notification recipient to delete."
        )

    class Meta:
        description = "Delete staff notification recipient."
        model = account_models.StaffNotificationRecipient
        object_type = StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"


class OrderSettingsUpdateInput(graphene.InputObjectType):
    automatically_confirm_all_new_orders = graphene.Boolean(
        required=False,
        description="When disabled, all new orders from checkout "
        "will be marked as unconfirmed. When enabled orders from checkout will "
        "become unfulfilled immediately.",
    )
    automatically_fulfill_non_shippable_gift_card = graphene.Boolean(
        required=False,
        description="When enabled, all non-shippable gift card orders "
        "will be fulfilled automatically.",
    )


class OrderSettingsUpdate(BaseMutation):
    order_settings = graphene.Field(OrderSettings, description="Order settings.")

    class Arguments:
        input = OrderSettingsUpdateInput(
            required=True, description="Fields required to update shop order settings."
        )

    class Meta:
        description = "Update shop order settings."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderSettingsError
        error_type_field = "order_settings_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        FIELDS = [
            "automatically_confirm_all_new_orders",
            "automatically_fulfill_non_shippable_gift_card",
        ]
        site = get_site_promise(info.context).get()
        instance = site.settings
        update_fields = []
        for field in FIELDS:
            value = data["input"].get(field)
            if value is not None:
                setattr(instance, field, value)
                update_fields.append(field)

        if update_fields:
            instance.save(update_fields=update_fields)
        return OrderSettingsUpdate(order_settings=instance)


class GiftCardSettingsUpdateInput(graphene.InputObjectType):
    expiry_type = GiftCardSettingsExpiryTypeEnum(
        description="Defines gift card default expiry settings."
    )
    expiry_period = TimePeriodInputType(description="Defines gift card expiry period.")


class GiftCardSettingsUpdate(BaseMutation):
    gift_card_settings = graphene.Field(
        GiftCardSettings, description="Gift card settings."
    )

    class Arguments:
        input = GiftCardSettingsUpdateInput(
            required=True, description="Fields required to update gift card settings."
        )

    class Meta:
        description = "Update gift card settings."
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardSettingsError

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        instance = site.settings
        input = data["input"]
        cls.clean_input(input, instance)

        expiry_period = input.get("expiry_period")
        instance.gift_card_expiry_period_type = (
            expiry_period["type"] if expiry_period else None
        )
        instance.gift_card_expiry_period = (
            expiry_period["amount"] if expiry_period else None
        )
        update_fields = ["gift_card_expiry_period", "gift_card_expiry_period_type"]

        if expiry_type := input.get("expiry_type"):
            instance.gift_card_expiry_type = expiry_type
            update_fields.append("gift_card_expiry_type")

        instance.save(update_fields=update_fields)
        return GiftCardSettingsUpdate(gift_card_settings=instance)

    @staticmethod
    def clean_input(input, instance):
        expiry_type = input.get("expiry_type") or instance.gift_card_expiry_type
        if (
            expiry_type == GiftCardSettingsExpiryType.EXPIRY_PERIOD
            and input.get("expiry_period") is None
        ):
            raise ValidationError(
                {
                    "expiry_period": ValidationError(
                        "Expiry period settings are required for expiry period "
                        "gift card settings.",
                        code=GiftCardSettingsErrorCode.REQUIRED.value,
                    )
                }
            )
        elif expiry_type == GiftCardSettingsExpiryType.NEVER_EXPIRE:
            input["expiry_period"] = None
