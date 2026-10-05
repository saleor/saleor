import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.utils.scoped_price_rows import (
    UNSET,
    ScopedPriceRowChanges,
    update_scoped_price_row,
)
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.enums import VariantChannelListingPriceErrorCode
from ....core.mutations import BaseMutation
from ....core.scalars import PositiveDecimal
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types.channels import VariantChannelListingPrice
from .utils import (
    VariantChannelListingPriceErrorBase,
    VariantChannelListingPriceScopeInput,
    clean_attribute_value_ids,
    clean_customer_type_ids,
    clean_price,
)


class VariantChannelListingPriceUpdateInput(VariantChannelListingPriceScopeInput):
    price = PositiveDecimal(
        description=(
            "The base price for the buyers in scope, in the listing currency. "
            "Cannot be null."
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = (
            "Fields to change on a scoped price. A field left out keeps its value. "
            "A list given replaces the whole set, null or an empty list clears it. "
            "A null window bound clears that bound." + ADDED_IN_324
        )


class VariantChannelListingPriceUpdateError(VariantChannelListingPriceErrorBase):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class VariantChannelListingPriceUpdate(BaseMutation):
    variant_channel_listing_price = graphene.Field(
        VariantChannelListingPrice, description="The updated scoped price."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of the scoped price to update.")
        input = VariantChannelListingPriceUpdateInput(
            required=True, description="Fields to change on the scoped price."
        )

    class Meta:
        description = (
            "Updates a scoped price of a variant in a channel. The resulting price "
            "must keep at least one condition." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = VariantChannelListingPriceUpdateError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
                description="A product variant was updated.",
            ),
        ]

    @classmethod
    def clean_price_change(cls, input, currency):
        if "price" not in input:
            return UNSET
        if input["price"] is None:
            raise ValidationError(
                {
                    "price": ValidationError(
                        "The price cannot be null. Leave it out to keep it.",
                        code=VariantChannelListingPriceErrorCode.REQUIRED.value,
                    )
                }
            )
        return clean_price(input["price"], currency)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        row = cls.get_node_or_error(
            info,
            id,
            only_type=VariantChannelListingPrice,
            qs=models.VariantChannelListingPrice.objects.select_related(
                "variant_channel_listing__variant"
            ),
        )
        listing = row.variant_channel_listing
        changes = ScopedPriceRowChanges(
            price_amount=cls.clean_price_change(input, listing.currency),
            customer_type_ids=(
                clean_customer_type_ids(cls, input["customer_types"] or [])
                if "customer_types" in input
                else UNSET
            ),
            attribute_value_ids=(
                clean_attribute_value_ids(cls, input["attribute_values"] or [])
                if "attribute_values" in input
                else UNSET
            ),
            valid_from=input["valid_from"] if "valid_from" in input else UNSET,
            valid_to=input["valid_to"] if "valid_to" in input else UNSET,
        )
        row = update_scoped_price_row(row, changes)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_variant_updated, listing.variant)
        return cls(variant_channel_listing_price=row)
