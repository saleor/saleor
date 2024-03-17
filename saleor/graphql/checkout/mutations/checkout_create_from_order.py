from typing import Any, Optional, cast

import graphene
from django.contrib.sites.models import Site

from ....checkout import models as checkout_models
from ....checkout.utils import add_variants_to_checkout
from ....core.exceptions import InsufficientStock
from ....core.utils.country import get_active_country
from ....order import models as order_models
from ....product import models as product_models
from ....product.models import ProductVariant
from ....warehouse.availability import check_stock_and_preorder_quantity_bulk
from ....warehouse.reservations import get_reservation_length, is_reservation_enabled
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_314, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.types import BaseObjectType, Error, common
from ...core.validators import get_not_available_variants_in_channel
from ...order.types import Order
from ...site.dataloaders import get_site_promise
from ..enums import (
    CheckoutCreateFromOrderErrorCode,
    CheckoutCreateFromOrderUnavailableVariantErrorCode,
)
from ..types import Checkout
from .utils import (
    CheckoutLineData,
    apply_gift_reward_if_applicable_on_checkout_creation,
    get_not_available_variants_for_purchase,
    get_not_published_variants,
    get_variants_and_total_quantities,
)


class CheckoutCreateFromOrderUnavailableVariant(BaseObjectType):
    message = graphene.String(description="The error message.", required=True)
    code = CheckoutCreateFromOrderUnavailableVariantErrorCode(
        description="The error code.", required=True
    )
    variant_id = graphene.ID(
        description="Variant ID that is unavailable.", required=True
    )
    line_id = graphene.ID(
        description="Order line ID that is unavailable.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutCreateFromOrderError(Error):
    code = CheckoutCreateFromOrderErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutCreateFromOrder(BaseMutation):
    unavailable_variants = common.NonNullList(
        CheckoutCreateFromOrderUnavailableVariant,
        description="Variants that were not attached to the checkout.",
    )
    checkout = graphene.Field(Checkout, description="Created checkout.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of a order that will be used to create the checkout.",
        )

    class Meta:
        description = (
            "Create new checkout from existing order." + ADDED_IN_314 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutCreateFromOrderError

    @classmethod
    def _create_variant_errors(
        cls, error_code: str, msg: str, order_lines: list[order_models.OrderLine]
    ) -> list[dict[str, Any]]:
        return [
            {
                "message": msg,
                "code": error_code,
                "variant_id": line.product_variant_id,
                "line_id": graphene.Node.to_global_id("OrderLine", line.pk),
            }
            for line in order_lines
        ]

    @classmethod
    def handle_not_available_variants_in_channel(
        cls,
        variant_ids_set: set[int],
        channel_id: int,
        order_lines: list[order_models.OrderLine],
        variant_errors: list[dict[str, Any]],
    ) -> set[int]:
        (
            not_available_in_channel,
            not_available_in_channel_graphql_ids,
        ) = get_not_available_variants_in_channel(variant_ids_set, channel_id)
        variant_ids_set = variant_ids_set - not_available_in_channel

        if not_available_in_channel:
            error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
            variant_errors.extend(
                cls._create_variant_errors(
                    error_code=error_codes.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
                    msg="Cannot add lines with unavailable variants.",
                    order_lines=[
                        line
                        for line in order_lines
                        if line.variant_id in not_available_in_channel
                    ],
                )
            )
        return variant_ids_set

    @classmethod
    def handle_not_found_variants(
        cls,
        order_lines: list[order_models.OrderLine],
        variant_errors: list[dict[str, Any]],
    ):
        error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
        lines_with_not_found_variants = (
            [line for line in order_lines if not line.variant_id],
        )
        if lines_with_not_found_variants:
            variant_errors.extend(
                cls._create_variant_errors(
                    error_code=error_codes.NOT_FOUND.value,
                    msg="Product variant not found",
                    order_lines=[line for line in order_lines if not line.variant_id],
                )
            )

    @classmethod
    def handle_not_published_variants(
        cls,
        variant_ids_set: set[int],
        channel_id: int,
        order_lines: list[order_models.OrderLine],
        variant_errors: list[dict[str, Any]],
    ) -> set[int]:
        not_published_ids, not_published_graphql_ids = get_not_published_variants(
            variant_ids_set, channel_id
        )
        variant_ids_set = variant_ids_set - not_published_ids

        if not_published_ids:
            error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
            variant_errors.extend(
                cls._create_variant_errors(
                    error_code=error_codes.PRODUCT_NOT_PUBLISHED.value,
                    msg="Cannot add lines for unpublished variants.",
                    order_lines=[
                        line
                        for line in order_lines
                        if line.variant_id in not_published_ids
                    ],
                )
            )
        return variant_ids_set

    @classmethod
    def handle_not_available_variants_for_purchase(
        cls,
        variant_ids_set: set[int],
        channel_id: int,
        order_lines: list[order_models.OrderLine],
        variant_errors: list[dict[str, Any]],
    ) -> set[int]:
        (
            not_available_for_purchase,
            not_available_for_purchase_graphql_ids,
        ) = get_not_available_variants_for_purchase(variant_ids_set, channel_id)
        variant_ids_set = variant_ids_set - not_available_for_purchase
        if not_available_for_purchase:
            error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
            variant_errors.extend(
                cls._create_variant_errors(
                    error_code=error_codes.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value,
                    msg="Cannot add lines for unavailable for purchase variants.",
                    order_lines=[
                        line
                        for line in order_lines
                        if line.variant_id in not_available_for_purchase
                    ],
                )
            )
        return variant_ids_set

    @classmethod
    def handle_variants_exceeding_quantity_limit(
        cls,
        variant_ids_set: set[int],
        order_lines: list[order_models.OrderLine],
        variant_errors: list[dict[str, Any]],
        global_quantity_limit: Optional[int],
    ) -> set[int]:
        variant_ids_to_exclude = []
        error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
        for line in order_lines:
            variant = line.variant
            variant = cast(ProductVariant, variant)
            quantity_limit = (
                variant.quantity_limit_per_customer or global_quantity_limit
            )
            if quantity_limit is not None and line.quantity > quantity_limit:
                msg = f"Cannot add more than {quantity_limit} "
                f"times this item: {line.variant}."
                variant_errors.append(
                    {
                        "message": msg,
                        "code": error_codes.QUANTITY_GREATER_THAN_LIMIT.value,
                        "variant_id": line.product_variant_id,
                        "line_id": graphene.Node.to_global_id("OrderLine", line.pk),
                    }
                )
                variant_ids_to_exclude.append(line.variant_id)
        return variant_ids_set - set(variant_ids_to_exclude)

    @classmethod
    def exclude_lines_unavailable_to_purchase(
        cls,
        order: order_models.Order,
        order_lines: list[order_models.OrderLine],
        global_quantity_limit: Optional[int],
    ) -> tuple[set[int], list[order_models.OrderLine], list[dict[str, Any]]]:
        variant_errors: list[dict[str, Any]] = []
        variant_ids_set = set(
            [line.variant_id for line in order_lines if line.variant_id]
        )
        channel_id = (order.channel_id,)
        channel_id = cast(int, channel_id)

        cls.handle_not_found_variants(
            order_lines=order_lines, variant_errors=variant_errors
        )

        order_lines = [line for line in order_lines if line.variant_id]

        variant_ids_set = cls.handle_not_available_variants_in_channel(
            variant_ids_set=variant_ids_set,
            channel_id=channel_id,
            order_lines=order_lines,
            variant_errors=variant_errors,
        )

        order_lines = [
            line for line in order_lines if line.variant_id in variant_ids_set
        ]

        variant_ids_set = cls.handle_not_published_variants(
            variant_ids_set=variant_ids_set,
            channel_id=channel_id,
            order_lines=order_lines,
            variant_errors=variant_errors,
        )

        order_lines = [
            line for line in order_lines if line.variant_id in variant_ids_set
        ]
        variant_ids_set = cls.handle_not_available_variants_for_purchase(
            variant_ids_set=variant_ids_set,
            channel_id=channel_id,
            order_lines=order_lines,
            variant_errors=variant_errors,
        )

        order_lines = [
            line for line in order_lines if line.variant_id in variant_ids_set
        ]
        variant_ids_set = cls.handle_variants_exceeding_quantity_limit(
            variant_ids_set, order_lines, variant_errors, global_quantity_limit
        )

        order_lines = [
            line for line in order_lines if line.variant_id in variant_ids_set
        ]
        return variant_ids_set, order_lines, variant_errors

    @classmethod
    def clean_order_lines(
        cls,
        order: order_models.Order,
        order_lines: list[order_models.OrderLine],
        site: Site,
    ):
        (
            variant_ids_set,
            available_order_lines,
            variant_errors,
        ) = cls.exclude_lines_unavailable_to_purchase(
            order=order,
            order_lines=order_lines,
            global_quantity_limit=site.settings.limit_quantity_per_checkout,
        )

        variants = list(
            product_models.ProductVariant.objects.select_related(
                "product__product_type"
            ).filter(id__in=variant_ids_set)
        )

        variants, quantities = get_variants_and_total_quantities(
            variants,
            [
                CheckoutLineData(
                    variant_id=str(line.variant_id), quantity=line.quantity
                )
                for line in order_lines
            ],
        )
        valid_order_lines: list[order_models.OrderLine] = []
        country = get_active_country(
            order.channel, order.shipping_address, order.billing_address
        )
        try:
            check_stock_and_preorder_quantity_bulk(
                variants,
                country,
                quantities,
                order.channel.slug,
                site.settings.limit_quantity_per_checkout,
                check_reservations=is_reservation_enabled(site.settings),
            )
            valid_order_lines = available_order_lines
        except InsufficientStock as e:
            variants_with_insufficient_stock = {
                item.variant.pk: item for item in e.items if item.variant
            }
            variant_ids_set = variant_ids_set - set(
                list(variants_with_insufficient_stock.keys())
            )
            error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
            for line in available_order_lines:
                variant_id = cast(int, line.variant_id)
                variant_with_insufficient_stock = variants_with_insufficient_stock.get(
                    variant_id
                )
                if not variant_with_insufficient_stock:
                    valid_order_lines.append(line)
                    continue
                msg = (
                    f"Could not add items {variant_with_insufficient_stock.variant}. "
                    f"Only {max(variant_with_insufficient_stock.available_quantity, 0)}"
                    f" remaining in stock.",
                )
                variant_errors.append(
                    {
                        "message": msg,
                        "code": error_codes.INSUFFICIENT_STOCK.value,
                        "variant_id": line.product_variant_id,
                        "line_id": graphene.Node.to_global_id("OrderLine", line.pk),
                    }
                )
        variants = product_models.ProductVariant.objects.filter(id__in=variant_ids_set)
        return variants, valid_order_lines, variant_errors

    @classmethod
    def create_checkout(
        cls,
        info: ResolveInfo,
        order: order_models.Order,
    ):
        user = info.context.user
        checkout = checkout_models.Checkout(
            channel_id=order.channel_id,
            currency=order.currency,
        )
        if user:
            checkout.user = user
            checkout.email = user.email
        checkout.save()
        return checkout

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id,
    ):
        site = get_site_promise(info.context).get()
        order = cls.get_node_or_error(
            info,
            id,
            field="id",
            only_type=Order,
            code=CheckoutCreateFromOrderErrorCode.ORDER_NOT_FOUND.value,
        )
        order_lines = order.lines.prefetch_related("variant").all()
        checkout = cls.create_checkout(info, order)
        variants, valid_order_lines, variant_errors = cls.clean_order_lines(
            order, order_lines, site
        )

        if variants and valid_order_lines:
            checkout = add_variants_to_checkout(
                checkout,
                variants,
                [
                    CheckoutLineData(
                        variant_id=str(line.variant_id), quantity=line.quantity
                    )
                    for line in valid_order_lines
                ],
                order.channel,
                site.settings.limit_quantity_per_checkout,
                reservation_length=get_reservation_length(
                    site=site, user=info.context.user
                ),
            )
        apply_gift_reward_if_applicable_on_checkout_creation(checkout)
        return CheckoutCreateFromOrder(
            checkout=checkout, unavailable_variants=variant_errors
        )
