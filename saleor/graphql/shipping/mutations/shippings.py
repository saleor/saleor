import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

from ....core.permissions import ShippingPermissions
from ....product import models as product_models
from ....shipping import models
from ....shipping.error_codes import ShippingErrorCode
from ....shipping.utils import (
    default_shipping_zone_exists,
    get_countries_without_shipping_zone,
)
from ...channel.types import ChannelContext
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import WeightScalar
from ...core.types.common import ShippingError
from ...core.utils import get_duplicates_ids
from ...product import types as product_types
from ...utils import resolve_global_ids_to_primary_keys
from ..enums import ShippingMethodTypeEnum
from ..types import ShippingMethod, ShippingMethodZipCodeRule, ShippingZone


class ShippingPriceInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the shipping method.")
    minimum_order_weight = WeightScalar(
        description="Minimum order weight to use this shipping method."
    )
    maximum_order_weight = WeightScalar(
        description="Maximum order weight to use this shipping method."
    )
    maximum_delivery_days = graphene.Int(
        description="Maximum number of days for delivery."
    )
    minimum_delivery_days = graphene.Int(
        description="Minimal number of days for delivery."
    )
    type = ShippingMethodTypeEnum(description="Shipping type: price or weight based.")
    shipping_zone = graphene.ID(
        description="Shipping zone this method belongs to.", name="shippingZone"
    )


class ShippingZoneCreateInput(graphene.InputObjectType):
    name = graphene.String(
        description="Shipping zone's name. Visible only to the staff."
    )
    description = graphene.String(description="Description of the shipping zone.")
    countries = graphene.List(
        graphene.String, description="List of countries in this shipping zone."
    )
    default = graphene.Boolean(
        description=(
            "Default shipping zone will be used for countries not covered by other "
            "zones."
        )
    )
    add_warehouses = graphene.List(
        graphene.ID,
        description="List of warehouses to assign to a shipping zone",
    )


class ShippingZoneUpdateInput(ShippingZoneCreateInput):
    remove_warehouses = graphene.List(
        graphene.ID,
        description="List of warehouses to unassign from a shipping zone",
    )


class ShippingZoneMixin:
    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        duplicates_ids = get_duplicates_ids(
            data.get("add_warehouses"), data.get("remove_warehouses")
        )
        if duplicates_ids:
            error_msg = (
                "The same object cannot be in both lists "
                "for adding and removing items."
            )
            raise ValidationError(
                {
                    "removeWarehouses": ValidationError(
                        error_msg,
                        code=ShippingErrorCode.DUPLICATED_INPUT_ITEM.value,
                        params={"warehouses": list(duplicates_ids)},
                    )
                }
            )

        cleaned_input = super().clean_input(info, instance, data)
        cleaned_input = cls.clean_default(instance, cleaned_input)
        return cleaned_input

    @classmethod
    def clean_default(cls, instance, data):
        default = data.get("default")
        if default:
            if default_shipping_zone_exists(instance.pk):
                raise ValidationError(
                    {
                        "default": ValidationError(
                            "Default shipping zone already exists.",
                            code=ShippingErrorCode.ALREADY_EXISTS.value,
                        )
                    }
                )
            else:
                countries = get_countries_without_shipping_zone()
                data["countries"] = countries
        else:
            data["default"] = False
        return data

    @classmethod
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)

        add_warehouses = cleaned_data.get("add_warehouses")
        if add_warehouses:
            instance.warehouses.add(*add_warehouses)

        remove_warehouses = cleaned_data.get("remove_warehouses")
        if remove_warehouses:
            instance.warehouses.remove(*remove_warehouses)


class ShippingZoneCreate(ShippingZoneMixin, ModelMutation):
    class Arguments:
        input = ShippingZoneCreateInput(
            description="Fields required to create a shipping zone.", required=True
        )

    class Meta:
        description = "Creates a new shipping zone."
        model = models.ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response


class ShippingZoneUpdate(ShippingZoneMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of a shipping zone to update.", required=True)
        input = ShippingZoneUpdateInput(
            description="Fields required to update a shipping zone.", required=True
        )

    class Meta:
        description = "Updates a new shipping zone."
        model = models.ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response


class ShippingZipCodeRulesCreateInputRange(graphene.InputObjectType):
    start = graphene.String(required=True, description="Start range of the zip code.")
    end = graphene.String(required=False, description="End range of the zip code.")


class ShippingZipCodeRulesCreateInput(graphene.InputObjectType):
    zip_code_rules = graphene.List(
        ShippingZipCodeRulesCreateInputRange,
        required=True,
        description="Zip code rules for shipping method.",
    )


class ShippingZipCodeRulesCreate(BaseMutation):
    zip_code_rules = graphene.List(
        ShippingMethodZipCodeRule,
        description="A shipping method zip code range.",
    )
    shipping_method = graphene.Field(
        ShippingMethod, description="Related shipping method."
    )

    class Arguments:
        shipping_method_id = graphene.ID(
            required=True, description="ID of a shipping method to assign."
        )
        input = ShippingZipCodeRulesCreateInput(
            description="Fields required to create a shipping zip codes.", required=True
        )

    class Meta:
        description = "Create a new zip code exclusion range for shipping method."
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        shipping_method = cls.get_node_or_error(
            info, data["shipping_method_id"], only_type=ShippingMethod
        )
        instances = []
        with transaction.atomic():
            for zip_range in data["input"]["zip_code_rules"]:
                try:
                    start = zip_range["start"]
                    end = zip_range["end"]
                    instance = models.ShippingMethodZipCodeRule.objects.create(
                        shipping_method=shipping_method,
                        start=start,
                        end=end,
                    )
                except IntegrityError:
                    raise ValidationError(
                        {
                            "zipCodeRules": ValidationError(
                                f"Entry start: {start}, end: {end} already exists.",
                                code=ShippingErrorCode.ALREADY_EXISTS.value,
                            )
                        }
                    )
                instances.append(instance)
        return ShippingZipCodeRulesCreate(
            zip_code_rules=instances,
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None),
        )


class ShippingZipCodeRulesDelete(ModelDeleteMutation):
    shipping_method = graphene.Field(
        ShippingMethod, description="Shipping method of deleted zip code rule."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a shipping method zip code to delete."
        )

    class Meta:
        description = "Deletes a shipping method zip code."
        model = models.ShippingMethodZipCodeRule
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_instance(info, **data)
        shipping_method = instance.shipping_method
        super().perform_mutation(_root, info, **data)
        return ShippingZipCodeRulesDelete(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )


class ShippingZoneDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping zone to delete.")

    class Meta:
        description = "Deletes a shipping zone."
        model = models.ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response


class ShippingPriceMixin:
    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data)
        errors = {}
        cls.clean_weight(cleaned_input, errors)
        if (
            "minimum_delivery_days" in cleaned_input
            or "maximum_delivery_days" in cleaned_input
        ):
            cls.clean_delivery_time(instance, cleaned_input, errors)
        if errors:
            raise ValidationError(errors)
        return cleaned_input

    @classmethod
    def clean_weight(cls, cleaned_input, errors):
        min_weight = cleaned_input.get("minimum_order_weight")
        max_weight = cleaned_input.get("maximum_order_weight")

        if min_weight and min_weight.value < 0:
            errors["minimum_order_weight"] = ValidationError(
                "Shipping can't have negative weight.",
                code=ShippingErrorCode.INVALID,
            )
        if max_weight and max_weight.value < 0:
            errors["maximum_order_weight"] = ValidationError(
                "Shipping can't have negative weight.",
                code=ShippingErrorCode.INVALID,
            )

        if errors:
            return

        if (
            min_weight is not None
            and max_weight is not None
            and max_weight <= min_weight
        ):
            raise ValidationError(
                {
                    "maximum_order_weight": ValidationError(
                        (
                            "Maximum order weight should be larger than the "
                            "minimum order weight."
                        ),
                        code=ShippingErrorCode.MAX_LESS_THAN_MIN,
                    )
                }
            )

    @classmethod
    def clean_delivery_time(cls, instance, cleaned_input, errors):
        """Validate delivery days.

        - check if minimum_delivery_days is not higher than maximum_delivery_days
        - check if minimum_delivery_days and maximum_delivery_days are positive values
        """
        min_delivery_days = (
            cleaned_input.get("minimum_delivery_days") or instance.minimum_delivery_days
        )
        max_delivery_days = (
            cleaned_input.get("maximum_delivery_days") or instance.maximum_delivery_days
        )

        if not min_delivery_days and not max_delivery_days:
            return

        error_occurred = False
        if min_delivery_days and min_delivery_days < 0:
            errors["minimum_delivery_days"] = ValidationError(
                "Minimum delivery days must be positive.",
                code=ShippingErrorCode.INVALID.value,
            )
            error_occurred = True
        if max_delivery_days and max_delivery_days < 0:
            errors["maximum_delivery_days"] = ValidationError(
                "Maximum delivery days must be positive.",
                code=ShippingErrorCode.INVALID.value,
            )
            error_occurred = True

        if error_occurred:
            return

        if (
            min_delivery_days is not None
            and max_delivery_days is not None
            and min_delivery_days > max_delivery_days
        ):
            if cleaned_input.get("minimum_delivery_days") is not None:
                error_msg = (
                    "Minimum delivery days should be lower "
                    "than maximum delivery days."
                )
                field = "minimum_delivery_days"
            else:
                error_msg = (
                    "Maximum delivery days should be higher than "
                    "minimum delivery days."
                )
                field = "maximum_delivery_days"
            errors[field] = ValidationError(
                error_msg, code=ShippingErrorCode.INVALID.value
            )


class ShippingPriceCreate(ShippingPriceMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )
    shipping_method = graphene.Field(
        ShippingMethod, description="A shipping method to create."
    )

    class Arguments:
        input = ShippingPriceInput(
            description="Fields required to create a shipping price.", required=True
        )

    class Meta:
        description = "Creates a new shipping price."
        model = models.ShippingMethod
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def success_response(cls, instance):
        shipping_method = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(shipping_method)
        response.shipping_zone = ChannelContext(
            node=instance.shipping_zone, channel_slug=None
        )
        return response


class ShippingPriceUpdate(ShippingPriceMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )
    shipping_method = graphene.Field(ShippingMethod, description="A shipping method.")

    class Arguments:
        id = graphene.ID(description="ID of a shipping price to update.", required=True)
        input = ShippingPriceInput(
            description="Fields required to update a shipping price.", required=True
        )

    class Meta:
        description = "Updates a new shipping price."
        model = models.ShippingMethod
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def success_response(cls, instance):
        shipping_method = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(shipping_method)

        response.shipping_zone = ChannelContext(
            node=instance.shipping_zone, channel_slug=None
        )
        return response


class ShippingPriceDelete(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethod, description="A shipping method to delete."
    )
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping price to delete.")

    class Meta:
        description = "Deletes a shipping price."
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        shipping_method = cls.get_node_or_error(
            info, data.get("id"), only_type=ShippingMethod
        )
        shipping_method_id = shipping_method.id
        shipping_zone = shipping_method.shipping_zone
        shipping_method.delete()
        shipping_method.id = shipping_method_id
        return ShippingPriceDelete(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None),
            shipping_zone=ChannelContext(node=shipping_zone, channel_slug=None),
        )


class ShippingPriceExcludeProductsInput(graphene.InputObjectType):
    products = graphene.List(
        graphene.ID,
        description="List of products which will be excluded.",
        required=True,
    )


class ShippingPriceExcludeProducts(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethod,
        description="A shipping method with new list of excluded products.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping price.")

        input = ShippingPriceExcludeProductsInput(
            description="Exclude products input.", required=True
        )

    class Meta:
        description = "Exclude products from shipping price."
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        shipping_method = cls.get_node_or_error(
            info, data.get("id"), only_type=ShippingMethod
        )
        input = data.get("input")
        product_ids = input.get("products", [])

        _, product_db_ids = resolve_global_ids_to_primary_keys(
            product_ids, product_types.Product
        )

        product_to_exclude = product_models.Product.objects.filter(
            id__in=product_db_ids
        )

        current_excluded_products = shipping_method.excluded_products.all()
        shipping_method.excluded_products.set(
            (current_excluded_products | product_to_exclude).distinct()
        )
        return ShippingPriceExcludeProducts(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )


class ShippingPriceRemoveProductFromExclude(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethod,
        description="A shipping method with new list of excluded products.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping price.")
        products = graphene.List(
            graphene.ID,
            required=True,
            description="List of products which will be removed from excluded list.",
        )

    class Meta:
        description = "Remove product from excluded list for shipping price."
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        shipping_method = cls.get_node_or_error(
            info, data.get("id"), only_type=ShippingMethod
        )
        product_ids = data.get("products")
        if product_ids:
            _, product_db_ids = resolve_global_ids_to_primary_keys(
                product_ids, product_types.Product
            )
            shipping_method.excluded_products.set(
                shipping_method.excluded_products.exclude(id__in=product_db_ids)
            )
        return ShippingPriceExcludeProducts(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )
