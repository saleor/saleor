from typing import TYPE_CHECKING, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ...account import models as account_models
from ...attribute import AttributeType
from ...attribute import models as attribute_models
from ...core.error_codes import ShopErrorCode
from ...core.permissions import OrderPermissions, PageTypePermissions, SitePermissions
from ...core.utils.url import validate_storefront_url
from ..account.i18n import I18nMixin
from ..account.types import AddressInput
from ..attribute.mutations import BaseReorderAttributesMutation
from ..attribute.types import Attribute
from ..core.enums import WeightUnitsEnum
from ..core.inputs import ReorderInput
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types.common import OrderSettingsError, ShopError
from ..core.utils import get_duplicates_ids
from ..core.utils.reordering import perform_reordering
from ..utils import resolve_global_ids_to_primary_keys
from .types import CategorySettings, OrderSettings, Shop

if TYPE_CHECKING:
    from ...site.models import SiteSettings


class ShopSettingsInput(graphene.InputObjectType):
    header_text = graphene.String(description="Header text.")
    description = graphene.String(description="SEO description.")
    include_taxes_in_prices = graphene.Boolean(description="Include taxes in prices.")
    display_gross_prices = graphene.Boolean(
        description="Display prices with tax in store."
    )
    charge_taxes_on_shipping = graphene.Boolean(description="Charge taxes on shipping.")
    track_inventory_by_default = graphene.Boolean(
        description="Enable inventory tracking."
    )
    default_weight_unit = WeightUnitsEnum(description="Default weight unit.")
    automatic_fulfillment_digital_products = graphene.Boolean(
        description="Enable automatic fulfillment for all digital products."
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
                    {"customer_set_password_url": error}, code=ShopErrorCode.INVALID
                )
        return data

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        for field_name, desired_value in cleaned_data.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)
        return instance

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = info.context.site.settings
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
    def perform_mutation(cls, _root, info, **data):
        site_settings = info.context.site.settings
        data = data.get("input")

        if data:
            if not site_settings.company_address:
                company_address = account_models.Address()
            else:
                company_address = site_settings.company_address
            company_address = cls.validate_address(data, company_address, info=info)
            company_address.save()
            site_settings.company_address = company_address
            site_settings.save(update_fields=["company_address"])
        else:
            if site_settings.company_address:
                site_settings.company_address.delete()
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
    def perform_mutation(cls, _root, info, **data):
        site = info.context.site
        data = data.get("input")
        domain = data.get("domain")
        name = data.get("name")
        if domain is not None:
            site.domain = domain
        if name is not None:
            site.name = name
        cls.clean_instance(info, site)
        site.save()
        return ShopDomainUpdate(shop=Shop())


class CategorySettingsInput(graphene.InputObjectType):
    add_attributes = graphene.List(
        graphene.NonNull(graphene.ID),
        description=(
            "List of attribute IDs that should be added to available "
            "category attributes."
        ),
        required=False,
    )
    remove_attributes = graphene.List(
        graphene.NonNull(graphene.ID),
        description=(
            "List of attribute IDs that should be removed from available "
            "category attributes."
        ),
        required=False,
    )


class CategorySettingsUpdate(BaseMutation):
    category_settings = graphene.Field(
        CategorySettings, description="Updated category settings."
    )

    class Arguments:
        input = CategorySettingsInput(
            required=True, description="Fields required to update category settings."
        )

    class Meta:
        description = "Updates category settings."
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        site_settings = info.context.site.settings
        input = data["input"]
        cleaned_input = cls.clean_input(site_settings, input)
        cls.update_category_settings(site_settings, cleaned_input)
        return cls(category_settings=CategorySettings())

    @classmethod
    def clean_input(cls, site_settings: "SiteSettings", input_data: dict):
        cls.validate_duplicates(input_data)

        remove_attrs = input_data.get("remove_attributes")
        if remove_attrs:
            input_data["remove_attributes"] = cls.get_nodes_or_error(
                remove_attrs, "id", Attribute
            )

        add_attrs = input_data.get("add_attributes")
        if add_attrs:
            _, pks = resolve_global_ids_to_primary_keys(add_attrs, Attribute)
            pks = cls.clean_add_attributes(pks, site_settings)
            input_data["add_attributes"] = attribute_models.Attribute.objects.filter(
                pk__in=pks
            )

        cls.validate_attribute_types(input_data.get("add_attributes", []))
        return input_data

    @staticmethod
    def validate_duplicates(input_data: dict):
        duplicated_ids = get_duplicates_ids(
            input_data.get("add_attributes"), input_data.get("remove_attributes")
        )
        if duplicated_ids:
            error_msg = (
                "The same object cannot be in both list"
                "for adding and removing items."
            )
            raise ValidationError(
                {
                    "input": ValidationError(
                        error_msg,
                        code=ShopErrorCode.DUPLICATED_INPUT_ITEM.value,
                        params={"attributes": list(duplicated_ids)},
                    )
                }
            )

    @staticmethod
    def clean_add_attributes(attr_ids: List[int], site_settings: "SiteSettings"):
        # drop attributes that are already assigned
        attr_ids = {int(id) for id in attr_ids}
        assigned_attr_ids = attribute_models.AttributeCategory.objects.filter(
            site_settings=site_settings, attribute_id__in=attr_ids
        ).values_list("attribute_id", flat=True)
        return set(attr_ids) - set(assigned_attr_ids)

    @staticmethod
    def validate_attribute_types(attributes: List[attribute_models.Attribute]):
        # only page attributes can be set as category attributes
        invalid_attrs = [
            attr for attr in attributes if attr.type != AttributeType.PAGE_TYPE
        ]
        if invalid_attrs:
            attr_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in invalid_attrs
            ]
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Only Page attributes can be set as category attributes.",
                        code=ShopErrorCode.INVALID.value,
                        params={"attributes": attr_ids},
                    )
                }
            )

    @staticmethod
    def update_category_settings(site_settings: "SiteSettings", cleaned_input: dict):
        remove_attr = cleaned_input.get("remove_attributes")
        add_attr = cleaned_input.get("add_attributes")
        if remove_attr:
            site_settings.category_attributes.filter(
                attribute_id__in=remove_attr
            ).delete()
        if add_attr:
            attribute_models.AttributeCategory.objects.bulk_create(
                [
                    attribute_models.AttributeCategory(
                        site_settings=site_settings, attribute=attr
                    )
                    for attr in add_attr
                ]
            )


class CategorySettingsReorderAttributes(BaseReorderAttributesMutation):
    category_settings = graphene.Field(
        CategorySettings, description="Reordered category settings."
    )

    class Meta:
        description = "Reorder the category settings attributes."
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    class Arguments:
        moves = graphene.List(
            ReorderInput,
            required=True,
            description="The list of attribute reordering operations.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, moves):
        site_settings = info.context.site.settings

        attributes_m2m = attribute_models.AttributeCategory.objects.filter(
            site_settings=site_settings
        )

        try:
            operations = cls.prepare_operations(moves, attributes_m2m)
        except ValidationError as error:
            error.code = ShopErrorCode.NOT_FOUND.value
            raise ValidationError({"moves": error})

        with transaction.atomic():
            perform_reordering(attributes_m2m, operations)

        return cls(category_settings=CategorySettings())


class ShopFetchTaxRates(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Meta:
        description = "Fetch tax rates."
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info):
        if not info.context.plugins.fetch_taxes_data():
            raise ValidationError(
                "Could not fetch tax rates. Make sure you have supplied a "
                "valid credential for your tax plugin.",
                code=ShopErrorCode.CANNOT_FETCH_TAX_RATES.value,
            )
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
                            code=ShopErrorCode.INVALID,
                        )
                    }
                )
            if not instance.id:
                raise ValidationError(
                    {
                        "staff_notification": ValidationError(
                            "User or email is required", code=ShopErrorCode.REQUIRED
                        )
                    }
                )
        if user and not user.is_staff:
            raise ValidationError(
                {
                    "user": ValidationError(
                        "User has to be staff user", code=ShopErrorCode.INVALID
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
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"


class OrderSettingsUpdateInput(graphene.InputObjectType):
    automatically_confirm_all_new_orders = graphene.Boolean(
        required=True,
        description="When disabled, all new orders from checkout "
        "will be marked as unconfirmed. When enabled orders from checkout will "
        "become unfulfilled immediately.",
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
    def perform_mutation(cls, _root, info, **data):
        instance = info.context.site.settings
        instance.automatically_confirm_all_new_orders = data["input"][
            "automatically_confirm_all_new_orders"
        ]
        instance.save(update_fields=["automatically_confirm_all_new_orders"])
        return OrderSettingsUpdate(order_settings=instance)
