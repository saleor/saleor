from django.core.exceptions import ValidationError
from django.db import transaction
from django_countries import countries

from ....channel.models import Channel
from ....inventory import PurchaseOrderItemStatus, events, models
from ....inventory.error_codes import PurchaseOrderErrorCode
from ....permission.enums import WarehousePermissions
from ....warehouse.models import Warehouse
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import DeprecatedModelMutation
from ...core.utils import from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import PurchaseOrder, PurchaseOrderCreateInput, PurchaseOrderError


class PurchaseOrderCreate(DeprecatedModelMutation):
    """Creates a new purchase order from a supplier.

    This mutation creates a purchase order in DRAFT status, allowing you to
    review the details before confirming it with the supplier.
    """

    class Arguments:
        input = PurchaseOrderCreateInput(
            required=True, description="Fields required to create a purchase order."
        )

    class Meta:
        description = "Creates a new purchase order from a supplier."
        model = models.PurchaseOrder
        object_type = PurchaseOrder
        permissions = (WarehousePermissions.MANAGE_PURCHASE_ORDERS,)
        error_type_class = PurchaseOrderError
        error_type_field = "purchase_order_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        """Validate input data before creating the purchase order."""
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        errors = {}

        # Validate source warehouse (must be non-owned/supplier)
        source_warehouse_id = data.get("source_warehouse_id")
        if source_warehouse_id:
            try:
                _, source_id = from_global_id_or_error(source_warehouse_id, "Warehouse")
                source_warehouse = Warehouse.objects.get(pk=source_id)

                if source_warehouse.is_owned:
                    errors["source_warehouse_id"] = ValidationError(
                        "Source warehouse must be a supplier (non-owned warehouse).",
                        code=PurchaseOrderErrorCode.WAREHOUSE_IS_OWNED.value,
                    )
                else:
                    cleaned_input["source_warehouse"] = source_warehouse
            except Warehouse.DoesNotExist:
                errors["source_warehouse_id"] = ValidationError(
                    "Source warehouse not found.",
                    code=PurchaseOrderErrorCode.INVALID_WAREHOUSE.value,
                )
        else:
            errors["source_warehouse_id"] = ValidationError(
                "This field is required.",
                code=PurchaseOrderErrorCode.REQUIRED.value,
            )

        # Validate destination warehouse (must be owned)
        destination_warehouse_id = data.get("destination_warehouse_id")
        if destination_warehouse_id:
            try:
                _, dest_id = from_global_id_or_error(
                    destination_warehouse_id, "Warehouse"
                )
                destination_warehouse = Warehouse.objects.get(pk=dest_id)

                if not destination_warehouse.is_owned:
                    errors["destination_warehouse_id"] = ValidationError(
                        "Destination warehouse must be an owned warehouse.",
                        code=PurchaseOrderErrorCode.WAREHOUSE_NOT_OWNED.value,
                    )
                else:
                    cleaned_input["destination_warehouse"] = destination_warehouse
            except Warehouse.DoesNotExist:
                errors["destination_warehouse_id"] = ValidationError(
                    "Destination warehouse not found.",
                    code=PurchaseOrderErrorCode.INVALID_WAREHOUSE.value,
                )
        else:
            errors["destination_warehouse_id"] = ValidationError(
                "This field is required.",
                code=PurchaseOrderErrorCode.REQUIRED.value,
            )

        # Validate channel (optional)
        channel_id = data.get("channel_id")
        if channel_id:
            try:
                _, ch_id = from_global_id_or_error(channel_id, "Channel")
                channel = Channel.objects.get(pk=ch_id)
                cleaned_input["channel"] = channel
            except Channel.DoesNotExist:
                errors["channel_id"] = ValidationError(
                    "Channel not found.",
                    code=PurchaseOrderErrorCode.INVALID.value,
                )

        # Validate items (optional for draft creation)
        items = data.get("items") or []
        if items:
            cleaned_items = []

            for idx, item in enumerate(items):
                item_errors = {}
                cleaned_item = {}

                # Validate variant
                variant_id = item.get("variant_id")
                if variant_id:
                    try:
                        _, variant_pk = from_global_id_or_error(
                            variant_id, "ProductVariant"
                        )
                        from ....product.models import ProductVariant

                        variant = ProductVariant.objects.get(pk=variant_pk)
                        cleaned_item["product_variant"] = variant
                    except ProductVariant.DoesNotExist:
                        item_errors["variant_id"] = ValidationError(
                            "Product variant not found.",
                            code=PurchaseOrderErrorCode.INVALID_VARIANT.value,
                        )

                # Validate quantity
                quantity = item.get("quantity_ordered")
                if quantity is not None:
                    if quantity <= 0:
                        item_errors["quantity_ordered"] = ValidationError(
                            "Quantity must be greater than 0.",
                            code=PurchaseOrderErrorCode.INVALID_QUANTITY.value,
                        )
                    else:
                        cleaned_item["quantity_ordered"] = quantity
                else:
                    item_errors["quantity_ordered"] = ValidationError(
                        "This field is required.",
                        code=PurchaseOrderErrorCode.REQUIRED.value,
                    )

                # Validate unit price (optional)
                unit_price = item.get("unit_price_amount")
                if unit_price is not None:
                    if unit_price <= 0:
                        item_errors["unit_price_amount"] = ValidationError(
                            "Unit price must be greater than 0.",
                            code=PurchaseOrderErrorCode.INVALID_PRICE.value,
                        )
                    else:
                        cleaned_item["unit_price_amount"] = unit_price

                # Validate currency (optional, basic 3-letter code check)
                currency = item.get("currency")
                if currency:
                    if not (len(currency) == 3 and currency.isalpha()):
                        item_errors["currency"] = ValidationError(
                            "Currency must be a valid 3-letter code.",
                            code=PurchaseOrderErrorCode.INVALID_CURRENCY.value,
                        )
                    else:
                        cleaned_item["currency"] = currency.upper()

                # Validate country of origin (optional)
                country_code = item.get("country_of_origin")
                if country_code:
                    if country_code.upper() not in dict(countries):
                        item_errors["country_of_origin"] = ValidationError(
                            "Invalid country code.",
                            code=PurchaseOrderErrorCode.INVALID_COUNTRY.value,
                        )
                    else:
                        cleaned_item["country_of_origin"] = country_code.upper()

                if item_errors:
                    # Flatten nested errors: items[0].field instead of items[0]: {field: error}
                    for field, error in item_errors.items():
                        errors[f"items[{idx}].{field}"] = error
                else:
                    cleaned_items.append(cleaned_item)

            if cleaned_items:
                cleaned_input["items"] = cleaned_items

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input, instance_tracker=None):
        """Create the purchase order and its items in a transaction."""
        app = get_app_promise(info.context).get()

        with transaction.atomic():
            # Save the purchase order instance with warehouses and channel
            instance.source_warehouse = cleaned_input["source_warehouse"]
            instance.destination_warehouse = cleaned_input["destination_warehouse"]
            if "channel" in cleaned_input:
                instance.channel = cleaned_input["channel"]
            if "name" in cleaned_input:
                instance.name = cleaned_input["name"]
            if "auto_reallocate_variants" in cleaned_input:
                instance.auto_reallocate_variants = cleaned_input[
                    "auto_reallocate_variants"
                ]
            instance.save()

            # Create purchase order items
            items = cleaned_input.get("items", [])
            for item_data in items:
                unit_price = item_data.get("unit_price_amount")
                total_price = (
                    unit_price * item_data["quantity_ordered"]
                    if unit_price is not None
                    else None
                )

                models.PurchaseOrderItem.objects.create(
                    order=instance,
                    product_variant=item_data["product_variant"],
                    quantity_ordered=item_data["quantity_ordered"],
                    total_price_amount=total_price,
                    currency=item_data.get("currency"),
                    country_of_origin=item_data.get("country_of_origin"),
                    status=PurchaseOrderItemStatus.DRAFT,
                )

            # Log the event for audit trail
            events.purchase_order_created_event(
                purchase_order=instance,
                user=info.context.user,
                app=app,
            )

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        """Trigger webhook after save."""
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.purchase_order_created, instance)
