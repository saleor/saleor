import graphene

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.utils.scoped_price_rows import delete_scoped_price_row
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.enums import VariantChannelListingPriceErrorCode
from ....core.mutations import BaseMutation
from ....core.types import Error
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types.channels import VariantChannelListingPrice


class VariantChannelListingPriceDeleteError(Error):
    code = VariantChannelListingPriceErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class VariantChannelListingPriceDelete(BaseMutation):
    variant_channel_listing_price = graphene.Field(
        VariantChannelListingPrice, description="The deleted scoped price."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of the scoped price to delete.")

    class Meta:
        description = "Deletes a scoped price of a variant in a channel." + ADDED_IN_324
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = VariantChannelListingPriceDeleteError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
                description="A product variant was updated.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id
    ):
        row = cls.get_node_or_error(
            info,
            id,
            only_type=VariantChannelListingPrice,
            qs=models.VariantChannelListingPrice.objects.select_related(
                "variant_channel_listing__variant"
            ),
        )
        db_id = row.pk
        delete_scoped_price_row(row)
        # the response carries the id of the deleted row
        row.pk = db_id
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(
            manager.product_variant_updated, row.variant_channel_listing.variant
        )
        return cls(variant_channel_listing_price=row)
