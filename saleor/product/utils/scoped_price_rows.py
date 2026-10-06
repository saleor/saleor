import datetime
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils import timezone

from ...attribute import AttributeInputType, AttributeType
from ...attribute.models import AttributeValue
from ...core.tracing import traced_atomic_transaction
from ...core.utils.unset import UNSET, Unset
from ..error_codes import VariantChannelListingPriceErrorCode
from ..lock_objects import (
    product_channel_listing_qs_select_for_update,
    variant_channel_listing_price_qs_select_for_update,
)
from ..models import (
    ProductVariantChannelListing,
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)
from .window_prices import mark_products_dirty_for_listings, sync_window_price_rows

MAX_SCOPED_PRICES_PER_LISTING = 100

SCOPED_PRICE_ATTRIBUTE_INPUT_TYPES = frozenset(
    {
        AttributeInputType.DROPDOWN,
        AttributeInputType.MULTISELECT,
        AttributeInputType.SWATCH,
        AttributeInputType.BOOLEAN,
    }
)


@dataclass(frozen=True)
class ScopedPriceRowData:
    """The complete desired state of a scoped price row."""

    price_amount: Decimal
    customer_type_ids: frozenset[int]
    attribute_value_ids: frozenset[int]
    valid_from: datetime.datetime | None
    valid_to: datetime.datetime | None

    @property
    def has_conditions(self) -> bool:
        return bool(
            self.customer_type_ids
            or self.attribute_value_ids
            or self.valid_from is not None
            or self.valid_to is not None
        )


@dataclass(frozen=True)
class ScopedPriceRowChanges:
    """The fields of a row to change. A field left unset keeps its value."""

    price_amount: Decimal | Unset = UNSET
    customer_type_ids: frozenset[int] | Unset = UNSET
    attribute_value_ids: frozenset[int] | Unset = UNSET
    valid_from: datetime.datetime | None | Unset = UNSET
    valid_to: datetime.datetime | None | Unset = UNSET


def validate_scoped_price_row_data(data: ScopedPriceRowData) -> None:
    """Reject a row that would have no scope or an empty validity window.

    A row without any condition would override the listing price for everyone,
    which is what the listing price itself is for. The window must be strictly
    ordered to match the database constraint.
    """
    if not data.has_conditions:
        raise ValidationError(
            "A scoped price needs at least one customer type, one attribute "
            "value or a validity window.",
            code=VariantChannelListingPriceErrorCode.REQUIRED.value,
        )
    if (
        data.valid_from is not None
        and data.valid_to is not None
        and data.valid_from >= data.valid_to
    ):
        raise ValidationError(
            {
                "valid_to": ValidationError(
                    "The end of the validity window must be after its start.",
                    code=VariantChannelListingPriceErrorCode.INVALID.value,
                )
            }
        )


def get_ineligible_attribute_value_ids(value_ids: Iterable[int]) -> set[int]:
    """Return the ids of the values that cannot scope a price.

    Only values of customer attributes with a fixed set of choices are eligible,
    because a buyer is matched by holding one of the listed values.
    """
    value_ids = list(value_ids)
    if not value_ids:
        return set()
    return {
        value_id
        for value_id, attribute_type, input_type in AttributeValue.objects.filter(
            pk__in=value_ids
        ).values_list("pk", "attribute__type", "attribute__input_type")
        if attribute_type != AttributeType.CUSTOMER_TYPE
        or input_type not in SCOPED_PRICE_ATTRIBUTE_INPUT_TYPES
    }


def create_scoped_price_row(
    listing: ProductVariantChannelListing,
    data: ScopedPriceRowData,
    now: datetime.datetime | None = None,
) -> VariantChannelListingPrice:
    """Create a scoped price row on the listing and fold it into the stored price.

    The product channel listing of the variant listing is locked while the cap
    is checked, so two concurrent creates cannot exceed it. Locking the existing
    rows would not do, as a row lock does not block an insert. The product
    channel listing is chosen over the variant listing because the dirty mark
    and the price refresh lock product channel listings first, and taking the
    locks in the same order everywhere rules out a deadlock between them.
    """
    now = now or timezone.now()
    validate_scoped_price_row_data(data)
    with traced_atomic_transaction():
        list(
            product_channel_listing_qs_select_for_update()
            .filter(channel_id=listing.channel_id, product__variants=listing.variant_id)
            .values_list("pk", flat=True)
        )
        row_count = VariantChannelListingPrice.objects.filter(
            variant_channel_listing_id=listing.pk
        ).count()
        if row_count >= MAX_SCOPED_PRICES_PER_LISTING:
            raise ValidationError(
                {
                    "variant_channel_listing": ValidationError(
                        "A variant channel listing can hold at most "
                        f"{MAX_SCOPED_PRICES_PER_LISTING} scoped prices.",
                        code=VariantChannelListingPriceErrorCode.LIMIT_EXCEEDED.value,
                    )
                }
            )
        row = VariantChannelListingPrice.objects.create(
            variant_channel_listing=listing,
            currency=listing.currency,
            price_amount=data.price_amount,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
        )
        _add_conditions(row, data.customer_type_ids, data.attribute_value_ids)
        sync_window_price_rows([row.pk], now)
    return row


def update_scoped_price_row(
    row: VariantChannelListingPrice,
    changes: ScopedPriceRowChanges,
    now: datetime.datetime | None = None,
) -> VariantChannelListingPrice:
    """Apply the changes to the row and refresh the stored price.

    The changes are merged with the current row under its lock, so two partial
    updates cannot revert each other, and the result is validated as a whole.
    Conditions are replaced as sets, only the differences are written. The sync
    re-evaluates whether the row still belongs in the stored price, which covers
    a moved window as well as buyer conditions added to an applied row. A price
    change of an applied row whose product is already being refreshed can be
    missed by that refresh and then reaches the stored price with the next
    refresh of the product, like a listing price change in the same situation.
    """
    now = now or timezone.now()
    with traced_atomic_transaction():
        locked_row = variant_channel_listing_price_qs_select_for_update().get(pk=row.pk)
        current_type_ids = frozenset(
            VariantChannelListingPriceCustomerType.objects.filter(
                listing_price_id=row.pk
            ).values_list("customer_type_id", flat=True)
        )
        current_value_ids = frozenset(
            VariantChannelListingPriceAttributeValue.objects.filter(
                listing_price_id=row.pk
            ).values_list("value_id", flat=True)
        )
        data = ScopedPriceRowData(
            price_amount=(
                locked_row.price_amount
                if changes.price_amount is UNSET
                else changes.price_amount
            ),
            customer_type_ids=(
                current_type_ids
                if changes.customer_type_ids is UNSET
                else changes.customer_type_ids
            ),
            attribute_value_ids=(
                current_value_ids
                if changes.attribute_value_ids is UNSET
                else changes.attribute_value_ids
            ),
            valid_from=(
                locked_row.valid_from
                if changes.valid_from is UNSET
                else changes.valid_from
            ),
            valid_to=(
                locked_row.valid_to if changes.valid_to is UNSET else changes.valid_to
            ),
        )
        validate_scoped_price_row_data(data)
        if removed_type_ids := current_type_ids - data.customer_type_ids:
            VariantChannelListingPriceCustomerType.objects.filter(
                listing_price_id=row.pk, customer_type_id__in=removed_type_ids
            ).delete()
        if removed_value_ids := current_value_ids - data.attribute_value_ids:
            VariantChannelListingPriceAttributeValue.objects.filter(
                listing_price_id=row.pk, value_id__in=removed_value_ids
            ).delete()
        _add_conditions(
            locked_row,
            data.customer_type_ids - current_type_ids,
            data.attribute_value_ids - current_value_ids,
        )
        locked_row.price_amount = data.price_amount
        locked_row.valid_from = data.valid_from
        locked_row.valid_to = data.valid_to
        locked_row.save(
            update_fields=("price_amount", "valid_from", "valid_to", "updated_at")
        )
        sync_window_price_rows([row.pk], now)
    return locked_row


def delete_scoped_price_row(row: VariantChannelListingPrice) -> None:
    """Delete the row and schedule a refresh of the stored price it may be in.

    A refresh that is already running when the row is deleted can store the
    deleted price, which then stays until the next refresh of the product, like
    a listing price change in the same situation.
    """
    with traced_atomic_transaction():
        locked_row_ids = list(
            variant_channel_listing_price_qs_select_for_update()
            .filter(pk=row.pk)
            .values_list("pk", flat=True)
        )
        if not locked_row_ids:
            return
        mark_products_dirty_for_listings([row.variant_channel_listing_id])
        VariantChannelListingPrice.objects.filter(pk__in=locked_row_ids).delete()


def _add_conditions(
    row: VariantChannelListingPrice,
    customer_type_ids: Iterable[int],
    attribute_value_ids: Iterable[int],
) -> None:
    VariantChannelListingPriceCustomerType.objects.bulk_create(
        [
            VariantChannelListingPriceCustomerType(
                listing_price=row, customer_type_id=customer_type_id
            )
            for customer_type_id in sorted(customer_type_ids)
        ]
    )
    VariantChannelListingPriceAttributeValue.objects.bulk_create(
        [
            VariantChannelListingPriceAttributeValue(
                listing_price=row, value_id=value_id
            )
            for value_id in sorted(attribute_value_ids)
        ]
    )


def count_scoped_price_rows_for_customer_type(customer_type_id: int) -> int:
    return VariantChannelListingPriceCustomerType.objects.filter(
        customer_type_id=customer_type_id
    ).count()


def count_scoped_price_rows_for_attribute_values(value_ids: Iterable[int]) -> int:
    """Return how many rows reference any of the values, each row counted once."""
    return (
        VariantChannelListingPriceAttributeValue.objects.filter(
            value_id__in=list(value_ids)
        )
        .values("listing_price_id")
        .distinct()
        .count()
    )


def count_scoped_price_rows_by_attribute_value_id(
    value_ids: Iterable[int],
) -> dict[int, int]:
    """Return how many rows reference each value, only for referenced values."""
    return dict(
        VariantChannelListingPriceAttributeValue.objects.filter(
            value_id__in=list(value_ids)
        )
        .values("value_id")
        .annotate(row_count=Count("listing_price_id", distinct=True))
        .values_list("value_id", "row_count")
    )


def count_scoped_price_rows_by_attribute_id(
    attribute_ids: Iterable[int],
) -> dict[int, int]:
    """Return how many rows reference a value of each attribute.

    Only referenced attributes are present. A row referencing two values of the
    same attribute is counted once.
    """
    return dict(
        VariantChannelListingPriceAttributeValue.objects.filter(
            value__attribute_id__in=list(attribute_ids)
        )
        .values("value__attribute_id")
        .annotate(row_count=Count("listing_price_id", distinct=True))
        .values_list("value__attribute_id", "row_count")
    )
