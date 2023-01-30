from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List

import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....discount import DiscountValueType
from ....discount.error_codes import DiscountErrorCode
from ....discount.models import SaleChannelListing
from ....permission.enums import DiscountPermissions
from ....product.tasks import update_products_discounted_prices_of_discount_task
from ...channel import ChannelContext
from ...channel.mutations import BaseChannelListingMutation
from ...core import ResolveInfo
from ...core.scalars import PositiveDecimal
from ...core.types import DiscountError, NonNullList
from ...core.validators import validate_price_precision
from ...discount.types import Sale
from ..dataloaders import SaleChannelListingBySaleIdLoader

if TYPE_CHECKING:
    from ....discount.models import Sale as SaleModel


class SaleChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    discount_value = PositiveDecimal(
        required=True, description="The value of the discount."
    )


class SaleChannelListingInput(graphene.InputObjectType):
    add_channels = NonNullList(
        SaleChannelListingAddInput,
        description="List of channels to which the sale should be assigned.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels from which the sale should be unassigned.",
        required=False,
    )


class SaleChannelListingUpdate(BaseChannelListingMutation):
    sale = graphene.Field(Sale, description="An updated sale instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleChannelListingInput(
            required=True,
            description="Fields required to update sale channel listings.",
        )

    class Meta:
        description = "Manage sale's availability in channels."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def add_channels(cls, sale: "SaleModel", add_channels: List[Dict]):
        for add_channel in add_channels:
            channel = add_channel["channel"]
            defaults = {"currency": channel.currency_code}
            channel = add_channel["channel"]
            if "discount_value" in add_channel.keys():
                defaults["discount_value"] = add_channel.get("discount_value")
            SaleChannelListing.objects.update_or_create(
                sale=sale,
                channel=channel,
                defaults=defaults,
            )

    @classmethod
    def clean_discount_values(
        cls,
        cleaned_channels,
        sale_type,
        errors: defaultdict[str, List[ValidationError]],
        error_code,
    ):
        channels_with_invalid_value_precision = []
        channels_with_invalid_percentage_value = []
        for cleaned_channel in cleaned_channels.get("add_channels", []):
            channel = cleaned_channel["channel"]
            currency_code = channel.currency_code
            discount_value = cleaned_channel.get("discount_value")
            if not discount_value:
                continue
            if sale_type == DiscountValueType.FIXED:
                try:
                    validate_price_precision(discount_value, currency_code)
                except ValidationError:
                    channels_with_invalid_value_precision.append(
                        cleaned_channel["channel_id"]
                    )
            elif sale_type == DiscountValueType.PERCENTAGE:
                if discount_value > 100:
                    channels_with_invalid_percentage_value.append(
                        cleaned_channel["channel_id"]
                    )

        if channels_with_invalid_value_precision:
            errors["input"].append(
                ValidationError(
                    "Invalid amount precision.",
                    code=error_code,
                    params={"channels": channels_with_invalid_value_precision},
                )
            )
        if channels_with_invalid_percentage_value:
            errors["input"].append(
                ValidationError(
                    "Invalid percentage value.",
                    code=error_code,
                    params={"channels": channels_with_invalid_percentage_value},
                )
            )
        return cleaned_channels

    @classmethod
    def remove_channels(cls, sale: "SaleModel", remove_channels: List[int]):
        sale.channel_listings.filter(channel_id__in=remove_channels).delete()

    @classmethod
    def save(cls, info: ResolveInfo, sale: "SaleModel", cleaned_input: Dict):
        with traced_atomic_transaction():
            cls.add_channels(sale, cleaned_input.get("add_channels", []))
            cls.remove_channels(sale, cleaned_input.get("remove_channels", []))
            update_products_discounted_prices_of_discount_task.delay(sale.pk)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        sale = cls.get_node_or_error(info, id, only_type=Sale, field="id")
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)
        cleaned_channels = cls.clean_channels(
            info, input, errors, DiscountErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_discount_values(
            cleaned_channels, sale.type, errors, DiscountErrorCode.INVALID.value
        )

        if errors:
            raise ValidationError(errors)

        cls.save(info, sale, cleaned_input)

        # Invalidate dataloader for channel listings
        SaleChannelListingBySaleIdLoader(info.context).clear(sale.id)

        return SaleChannelListingUpdate(
            sale=ChannelContext(node=sale, channel_slug=None)
        )
