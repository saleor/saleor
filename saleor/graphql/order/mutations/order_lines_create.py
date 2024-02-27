from collections import defaultdict, namedtuple

import graphene
from django.core.exceptions import ValidationError

from ....core.taxes import TaxError
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_lines
from ....order.search import update_order_search_vector
from ....order.utils import (
    add_variant_to_order,
    invalidate_order_prices,
    recalculate_order_weight,
)
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import ProductVariant
from ..types import Order, OrderLine
from ..utils import (
    OrderLineData,
    validate_product_is_published_in_channel,
    validate_variant_channel_listings,
)
from .draft_order_create import OrderLineCreateInput
from .utils import (
    EditableOrderValidationMixin,
    get_variant_rule_info_map,
    get_webhook_handler_by_order_status,
)

VariantData = namedtuple("VariantData", ["variant", "rules_info"])


class OrderLinesCreate(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="Related order.")
    order_lines = NonNullList(OrderLine, description="List of added order lines.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the order to add the lines to."
        )
        input = NonNullList(
            OrderLineCreateInput,
            required=True,
            description="Fields required to add order lines.",
        )

    class Meta:
        description = "Create order lines for an order."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        errors_mapping = {"lines": "input", "channel": "input"}

    @classmethod
    def validate_lines(
        cls, info: ResolveInfo, data, existing_lines_info, variants_data
    ):
        grouped_lines_data: list[OrderLineData] = []
        lines_data_map: dict[str, OrderLineData] = defaultdict(OrderLineData)

        variants_from_existing_lines = [
            line_info.line.variant_id for line_info in existing_lines_info
        ]

        invalid_ids = []
        for input_line in data:
            variant_id: str = input_line["variant_id"]
            force_new_line = input_line["force_new_line"]
            variant_data = variants_data.get(variant_id)
            variant = variant_data.variant
            quantity = input_line["quantity"]

            custom_price = input_line.get("price")
            if quantity > 0:
                if force_new_line or variants_from_existing_lines.count(variant.pk) > 1:
                    grouped_lines_data.append(
                        OrderLineData(
                            variant_id=str(variant.id),
                            variant=variant,
                            quantity=quantity,
                            price_override=custom_price,
                            rules_info=variant_data.rules_info,
                        )
                    )
                else:
                    line_id = cls._find_line_id_for_variant_if_exist(
                        variant.pk, existing_lines_info
                    )

                    if line_id:
                        line_data = lines_data_map[line_id]
                        line_data.line_id = line_id
                    else:
                        line_data = lines_data_map[str(variant.id)]
                        line_data.variant_id = str(variant.id)

                    line_data.variant = variant
                    line_data.quantity += quantity
                    line_data.price_override = custom_price
                    line_data.rules_info = variant_data.rules_info
            else:
                invalid_ids.append(variant_id)
        if invalid_ids:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Variants quantity must be greater than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY.value,
                        params={"variants": invalid_ids},
                    ),
                }
            )

        grouped_lines_data += list(lines_data_map.values())
        return grouped_lines_data

    @classmethod
    def validate_variants(cls, order, variants):
        try:
            channel = order.channel
            validate_product_is_published_in_channel(variants, channel)
            validate_variant_channel_listings(variants, channel)
        except ValidationError as error:
            cls.remap_error_fields(error, cls._meta.errors_mapping)
            raise ValidationError(error)

    @staticmethod
    def add_lines_to_order(order, lines_data, user, app, manager):
        added_lines: list[OrderLine] = []
        try:
            for line_data in lines_data:
                line = add_variant_to_order(
                    order,
                    line_data,
                    user,
                    app,
                    manager,
                    allocate_stock=order.is_unconfirmed(),
                )
                added_lines.append(line)
        except TaxError as tax_error:
            raise ValidationError(
                f"Unable to calculate taxes - {str(tax_error)}",
                code=OrderErrorCode.TAX_ERROR.value,
            )
        return added_lines

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])
        cls.validate_order(order)
        existing_lines_info = fetch_order_lines(order)
        variant_pks = cls.get_global_ids_or_error(
            [line["variant_id"] for line in input], ProductVariant, "variant_id"
        )
        variants_data = get_variant_rule_info_map(
            variant_pks, order.channel_id, order.language_code
        )

        lines_to_add = cls.validate_lines(
            info, input, existing_lines_info, variants_data
        )
        variants = [line.variant for line in lines_to_add]
        cls.validate_variants(order, variants)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            added_lines = cls.add_lines_to_order(
                order,
                lines_to_add,
                info.context.user,
                app,
                manager,
            )

            # Create the products added event
            events.order_added_products_event(
                order=order,
                user=info.context.user,
                app=app,
                order_lines=added_lines,
            )

            invalidate_order_prices(order)
            recalculate_order_weight(order)
            update_order_search_vector(order, save=False)
            order.save(
                update_fields=[
                    "should_refresh_prices",
                    "weight",
                    "search_vector",
                    "updated_at",
                ]
            )
            func = get_webhook_handler_by_order_status(order.status, manager)
            cls.call_event(func, order)

        return OrderLinesCreate(order=order, order_lines=added_lines)

    @classmethod
    def _find_line_id_for_variant_if_exist(cls, variant_id, lines_info):
        """Return line id by using provided variantId parameter."""
        if not lines_info:
            return

        line_info = list(
            filter(
                lambda x: (x.variant and x.variant.pk == int(variant_id)), lines_info
            )
        )

        if not line_info or len(line_info) > 1:
            return

        return str(line_info[0].line.id)
