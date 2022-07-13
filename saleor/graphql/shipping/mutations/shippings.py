from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef
from django.db.utils import IntegrityError

from ....channel import models as channel_models
from ....core.permissions import ShippingPermissions
from ....core.tracing import traced_atomic_transaction
from ....product import models as product_models
from ....shipping import models
from ....shipping.error_codes import ShippingErrorCode
from ....shipping.tasks import (
    drop_invalid_shipping_methods_relations_for_given_channels,
)
from ....shipping.utils import (
    default_shipping_zone_exists,
    get_countries_without_shipping_zone,
)
from ...channel.types import ChannelContext
from ...core.fields import JSONString
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import WeightScalar
from ...core.types import NonNullList, ShippingError
from ...product import types as product_types
from ...shipping import types as shipping_types
from ...utils import resolve_global_ids_to_primary_keys
from ...utils.validators import check_for_duplicates
from ..enums import PostalCodeRuleInclusionTypeEnum, ShippingMethodTypeEnum
from ..types import ShippingMethodPostalCodeRule, ShippingMethodType, ShippingZone


class ShippingPostalCodeRulesCreateInputRange(graphene.InputObjectType):
    start = graphene.String(
        required=True, description="Start range of the postal code."
    )
    end = graphene.String(required=False, description="End range of the postal code.")


class ShippingPriceInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the shipping method.")
    description = JSONString(description="Shipping method description.")
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
    add_postal_code_rules = NonNullList(
        ShippingPostalCodeRulesCreateInputRange,
        description="Postal code rules to add.",
    )
    delete_postal_code_rules = NonNullList(
        graphene.ID,
        description="Postal code rules to delete.",
    )
    inclusion_type = PostalCodeRuleInclusionTypeEnum(
        description="Inclusion type for currently assigned postal code rules.",
    )


class ShippingZoneCreateInput(graphene.InputObjectType):
    name = graphene.String(
        description="Shipping zone's name. Visible only to the staff."
    )
    description = graphene.String(description="Description of the shipping zone.")
    countries = NonNullList(
        graphene.String, description="List of countries in this shipping zone."
    )
    default = graphene.Boolean(
        description=(
            "Default shipping zone will be used for countries not covered by other "
            "zones."
        )
    )
    add_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to assign to a shipping zone",
    )
    add_channels = NonNullList(
        graphene.ID,
        description="List of channels to assign to the shipping zone.",
    )


class ShippingZoneUpdateInput(ShippingZoneCreateInput):
    remove_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to unassign from a shipping zone",
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels to unassign from the shipping zone.",
    )


class ShippingZoneMixin:
    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        errors = defaultdict(list)
        cls.check_duplicates(
            errors, data, "add_warehouses", "remove_warehouses", "warehouses"
        )
        cls.check_duplicates(
            errors, data, "add_channels", "remove_channels", "channels"
        )

        if errors:
            raise ValidationError(errors)

        cleaned_input = super().clean_input(info, instance, data)
        if add_warehouses := cleaned_input.get("add_warehouses"):
            cls.clean_add_warehouses(instance, add_warehouses, cleaned_input)
        cleaned_input = cls.clean_default(instance, cleaned_input)
        return cleaned_input

    @classmethod
    def check_duplicates(
        cls,
        errors: dict,
        input_data: dict,
        add_field: str,
        remove_field: str,
        error_class_field: str,
    ):
        """Check if any items are on both input field.

        Raise error if some of items are duplicated.
        """
        error = check_for_duplicates(
            input_data, add_field, remove_field, error_class_field
        )
        if error:
            error.code = ShippingErrorCode.DUPLICATED_INPUT_ITEM.value
            errors[error_class_field].append(error)

    @classmethod
    def clean_add_warehouses(cls, shipping_zone, warehouses, cleaned_input):
        """Check if all warehouses to add has common channel with shipping zone.

        Raise and error when the condition is not fulfilled.
        """
        warehouse_ids = [warehouse.id for warehouse in warehouses]

        remove_channel_ids = set()
        if remove_channels := cleaned_input.get("remove_channels"):
            remove_channel_ids = {channel.id for channel in remove_channels}

        add_channel_ids = set()
        if add_channels := cleaned_input.get("add_channels"):
            add_channel_ids = {channel.id for channel in add_channels}

        ChannelWarehouse = channel_models.Channel.warehouses.through
        channel_warehouses = ChannelWarehouse.objects.filter(
            warehouse_id__in=warehouse_ids
        )

        # any warehouse from the list cannot be assigned when:
        # 1) where there are no channels assigned to any warehouse
        # 2) any channel is will be not assigned to the shipping zone
        if not channel_warehouses or (not shipping_zone.id and not add_channel_ids):
            invalid_warehouse_ids = warehouse_ids

        warehouse_to_channel_mapping = defaultdict(set)
        for warehouse_id, channel_id in channel_warehouses.values_list(
            "warehouse_id", "channel_id"
        ):
            warehouse_to_channel_mapping[warehouse_id].add(channel_id)

        # if the shipping zone does not exist yet, all zone channels will be channels
        # provided in `add_channels` field
        shipping_zone_channel_ids = (
            add_channel_ids
            if not shipping_zone.id
            else cls._get_shipping_zone_channel_ids(
                shipping_zone, remove_channel_ids, add_channel_ids
            )
        )

        invalid_warehouse_ids = cls._find_invalid_warehouses(
            warehouse_to_channel_mapping, warehouse_ids, shipping_zone_channel_ids
        )

        if invalid_warehouse_ids:
            invalid_warehouses = {
                graphene.Node.to_global_id("Warehouse", pk)
                for pk in invalid_warehouse_ids
            }
            raise ValidationError(
                {
                    "add_warehouses": ValidationError(
                        "Only warehouses that have common channel with shipping zone "
                        "can be assigned.",
                        code=ShippingErrorCode.INVALID,
                        params={
                            "warehouses": invalid_warehouses,
                        },
                    )
                }
            )

    @staticmethod
    def _get_shipping_zone_channel_ids(
        shipping_zone, remove_channel_ids, add_channel_ids
    ):
        # get shipping zone channels
        ShippingZoneChannel = models.ShippingZone.channels.through
        shipping_zone_channel_ids = set(
            ShippingZoneChannel.objects.filter(shippingzone_id=shipping_zone.id)
            .exclude(channel_id__in=remove_channel_ids)
            .values_list("channel_id", flat=True)
        )
        # shipping zone channels set need to be updated with channels
        # that will be removed and added to shipping zone
        return shipping_zone_channel_ids | add_channel_ids

    @staticmethod
    def _find_invalid_warehouses(
        warehouse_to_channel_mapping, warehouse_ids, zone_channel_ids
    ):
        invalid_warehouse_ids = []
        for warehouse_id in warehouse_ids:
            warehouse_channels = warehouse_to_channel_mapping.get(warehouse_id)
            # warehouse cannot be added if it hasn't got any channel assigned
            # or if it does not have common channel with shipping zone
            if not warehouse_channels or not warehouse_channels.intersection(
                zone_channel_ids
            ):
                invalid_warehouse_ids.append(warehouse_id)
        return invalid_warehouse_ids

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
                data["countries"].extend([country for country in countries])
        else:
            data["default"] = False
        return data

    @classmethod
    @traced_atomic_transaction()
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)

        add_warehouses = cleaned_data.get("add_warehouses")
        if add_warehouses:
            instance.warehouses.add(*add_warehouses)

        remove_warehouses = cleaned_data.get("remove_warehouses")
        if remove_warehouses:
            instance.warehouses.remove(*remove_warehouses)

        add_channels = cleaned_data.get("add_channels")
        if add_channels:
            instance.channels.add(*add_channels)

        remove_channels = cleaned_data.get("remove_channels")
        if remove_channels:
            instance.channels.remove(*remove_channels)
            shipping_channel_listings = (
                models.ShippingMethodChannelListing.objects.filter(
                    shipping_method__shipping_zone=instance, channel__in=remove_channels
                )
            )
            shipping_method_ids = list(
                shipping_channel_listings.values_list("shipping_method_id", flat=True)
            )
            shipping_channel_listings.delete()
            channel_ids = [channel.id for channel in remove_channels]
            cls.delete_invalid_shipping_zone_to_warehouse_relation(instance)
            drop_invalid_shipping_methods_relations_for_given_channels.delay(
                shipping_method_ids, channel_ids
            )

    @classmethod
    def delete_invalid_shipping_zone_to_warehouse_relation(cls, shipping_zone):
        """Drop zone-warehouse relations that becomes invalid after channels deletion.

        Remove all shipping zone to warehouse relations that will not have common
        channel after removing given channels from the shipping zone.
        """
        WarehouseShippingZone = models.ShippingZone.warehouses.through
        ChannelWarehouse = channel_models.Channel.warehouses.through
        ShippingZoneChannel = models.ShippingZone.channels.through

        warehouse_shipping_zones = WarehouseShippingZone.objects.filter(
            shippingzone_id=shipping_zone.id
        )

        channel_warehouses = ChannelWarehouse.objects.filter(
            Exists(
                warehouse_shipping_zones.filter(warehouse_id=OuterRef("warehouse_id"))
            )
        )

        warehouse_to_channel_mapping = defaultdict(set)
        for warehouse_id, channel_id in channel_warehouses.values_list(
            "warehouse_id", "channel_id"
        ):
            warehouse_to_channel_mapping[warehouse_id].add(channel_id)

        shipping_zone_channel_ids = set(
            ShippingZoneChannel.objects.filter(
                shippingzone_id=shipping_zone.id
            ).values_list("channel_id", flat=True)
        )

        shipping_zone_warehouses_to_delete = []
        for id, warehouse_id in warehouse_shipping_zones.values_list(
            "id", "warehouse_id"
        ):
            warehouse_channels = warehouse_to_channel_mapping.get(warehouse_id, set())
            # if there is no common channels between shipping zone and warehouse
            # the relation should be deleted
            if not warehouse_channels or not warehouse_channels.intersection(
                shipping_zone_channel_ids
            ):
                shipping_zone_warehouses_to_delete.append(id)

        WarehouseShippingZone.objects.filter(
            id__in=shipping_zone_warehouses_to_delete
        ).delete()


class ShippingZoneCreate(ShippingZoneMixin, ModelMutation):
    class Arguments:
        input = ShippingZoneCreateInput(
            description="Fields required to create a shipping zone.", required=True
        )

    class Meta:
        description = "Creates a new shipping zone."
        model = models.ShippingZone
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        info.context.plugins.shipping_zone_created(instance)

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
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        info.context.plugins.shipping_zone_updated(instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response


class ShippingZoneDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping zone to delete.")

    class Meta:
        description = "Deletes a shipping zone."
        model = models.ShippingZone
        object_type = ShippingZone
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        info.context.plugins.shipping_zone_deleted(instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)

        return response


class ShippingMethodTypeMixin:
    @classmethod
    def get_type_for_model(cls):
        return shipping_types.ShippingMethodType

    @classmethod
    def get_instance(cls, info, **data):
        object_id = data.get("id")
        if object_id:
            instance = cls.get_node_or_error(
                info, object_id, qs=models.ShippingMethod.objects
            )
        else:
            instance = cls._meta.model()
        return instance


class ShippingPriceMixin:
    @classmethod
    def get_type_for_model(cls):
        return ShippingMethodType

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

        if cleaned_input.get("delete_postal_code_rules"):
            _, postal_code_rules_db_ids = resolve_global_ids_to_primary_keys(
                data["delete_postal_code_rules"], ShippingMethodPostalCodeRule
            )
            cleaned_input["delete_postal_code_rules"] = postal_code_rules_db_ids
        if cleaned_input.get("add_postal_code_rules") and not cleaned_input.get(
            "inclusion_type"
        ):
            raise ValidationError(
                {
                    "inclusion_type": ValidationError(
                        "This field is required.",
                        code=ShippingErrorCode.REQUIRED,
                    )
                }
            )

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

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)

        delete_postal_code_rules = cleaned_input.get("delete_postal_code_rules")
        if delete_postal_code_rules:
            instance.postal_code_rules.filter(id__in=delete_postal_code_rules).delete()

        if cleaned_input.get("add_postal_code_rules"):
            inclusion_type = cleaned_input["inclusion_type"]
            for postal_code_rule in cleaned_input["add_postal_code_rules"]:
                start = postal_code_rule["start"]
                end = postal_code_rule.get("end")
                try:
                    instance.postal_code_rules.create(
                        start=start, end=end, inclusion_type=inclusion_type
                    )
                except IntegrityError:
                    raise ValidationError(
                        {
                            "addPostalCodeRules": ValidationError(
                                f"Entry start: {start}, end: {end} already exists.",
                                code=ShippingErrorCode.ALREADY_EXISTS.value,
                            )
                        }
                    )


class ShippingPriceCreate(ShippingPriceMixin, ShippingMethodTypeMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )
    shipping_method = graphene.Field(
        ShippingMethodType, description="A shipping method to create."
    )

    class Arguments:
        input = ShippingPriceInput(
            description="Fields required to create a shipping price.", required=True
        )

    class Meta:
        description = "Creates a new shipping price."
        model = models.ShippingMethod
        object_type = ShippingMethodType
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        info.context.plugins.shipping_price_created(instance)

    @classmethod
    def success_response(cls, instance):
        shipping_method = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(shipping_method)
        response.shipping_zone = ChannelContext(
            node=instance.shipping_zone, channel_slug=None
        )
        return response


class ShippingPriceUpdate(ShippingPriceMixin, ShippingMethodTypeMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )
    shipping_method = graphene.Field(
        ShippingMethodType, description="A shipping method."
    )

    class Arguments:
        id = graphene.ID(description="ID of a shipping price to update.", required=True)
        input = ShippingPriceInput(
            description="Fields required to update a shipping price.", required=True
        )

    class Meta:
        description = "Updates a new shipping price."
        model = models.ShippingMethod
        object_type = ShippingMethodType
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        info.context.plugins.shipping_price_updated(instance)

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
        ShippingMethodType, description="A shipping method to delete."
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
            info, data.get("id"), qs=models.ShippingMethod.objects
        )
        shipping_method_id = shipping_method.id
        shipping_zone = shipping_method.shipping_zone
        shipping_method.delete()
        shipping_method.id = shipping_method_id

        info.context.plugins.shipping_price_deleted(shipping_method)

        return ShippingPriceDelete(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None),
            shipping_zone=ChannelContext(node=shipping_zone, channel_slug=None),
        )


class ShippingPriceExcludeProductsInput(graphene.InputObjectType):
    products = NonNullList(
        graphene.ID,
        description="List of products which will be excluded.",
        required=True,
    )


class ShippingPriceExcludeProducts(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethodType,
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
            info, data.get("id"), qs=models.ShippingMethod.objects
        )
        input = data.get("input")
        product_ids = input.get("products", [])

        product_db_ids = cls.get_global_ids_or_error(
            product_ids, product_types.Product, field="products"
        )

        product_to_exclude = product_models.Product.objects.filter(
            id__in=product_db_ids
        )

        current_excluded_products = shipping_method.excluded_products.all()
        shipping_method.excluded_products.set(
            (current_excluded_products | product_to_exclude).distinct()
        )

        info.context.plugins.shipping_price_updated(shipping_method)

        return ShippingPriceExcludeProducts(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )


class ShippingPriceRemoveProductFromExclude(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethodType,
        description="A shipping method with new list of excluded products.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping price.")
        products = NonNullList(
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
            info, data.get("id"), qs=models.ShippingMethod.objects
        )

        product_ids = data.get("products")
        if product_ids:
            product_db_ids = cls.get_global_ids_or_error(
                product_ids, product_types.Product, field="products"
            )
            shipping_method.excluded_products.set(
                shipping_method.excluded_products.exclude(id__in=product_db_ids)
            )

        info.context.plugins.shipping_price_updated(shipping_method)

        return ShippingPriceExcludeProducts(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )
