import graphene

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.utils.scoped_price_rows import (
    ScopedPriceRowData,
    create_scoped_price_row,
)
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.scalars import PositiveDecimal
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types.channels import (
    ProductVariantChannelListing,
    VariantChannelListingPrice,
)
from .utils import (
    VariantChannelListingPriceErrorBase,
    VariantChannelListingPriceScopeInput,
    clean_attribute_value_ids,
    clean_customer_type_ids,
    clean_price,
)


class VariantChannelListingPriceCreateInput(VariantChannelListingPriceScopeInput):
    variant_channel_listing = graphene.ID(
        required=True,
        description="ID of the variant channel listing the price belongs to.",
    )
    price = PositiveDecimal(
        required=True,
        description="The base price for the buyers in scope, in the listing currency.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Fields required to create a scoped price." + ADDED_IN_324


class VariantChannelListingPriceCreateError(VariantChannelListingPriceErrorBase):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class VariantChannelListingPriceCreate(BaseMutation):
    variant_channel_listing_price = graphene.Field(
        VariantChannelListingPrice, description="The created scoped price."
    )

    class Arguments:
        input = VariantChannelListingPriceCreateInput(
            required=True, description="Fields required to create a scoped price."
        )

    class Meta:
        description = (
            "Creates a scoped price of a variant in a channel. At least one "
            "condition is required. A listing holds at most 100 scoped prices."
            + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = VariantChannelListingPriceCreateError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
                description="A product variant was updated.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        listing = cls.get_node_or_error(
            info,
            input["variant_channel_listing"],
            field="variant_channel_listing",
            only_type=ProductVariantChannelListing,
            qs=models.ProductVariantChannelListing.objects.select_related("variant"),
        )
        data = ScopedPriceRowData(
            price_amount=clean_price(input["price"], listing.currency),
            customer_type_ids=clean_customer_type_ids(
                cls, input.get("customer_types") or []
            ),
            attribute_value_ids=clean_attribute_value_ids(
                cls, input.get("attribute_values") or []
            ),
            valid_from=input.get("valid_from"),
            valid_to=input.get("valid_to"),
        )
        row = create_scoped_price_row(listing, data)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_variant_updated, listing.variant)
        return cls(variant_channel_listing_price=row)
