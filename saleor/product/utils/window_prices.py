import datetime
from collections.abc import Iterable

from django.db import transaction
from django.db.models import Exists, OuterRef, Q

from ..lock_objects import variant_channel_listing_price_qs_select_for_update
from ..models import (
    ProductChannelListing,
    ProductVariantChannelListing,
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)


def _annotate_buyer_conditions(queryset):
    return queryset.annotate(
        has_buyer_conditions=Exists(
            VariantChannelListingPriceCustomerType.objects.filter(
                listing_price_id=OuterRef("pk")
            )
        )
        | Exists(
            VariantChannelListingPriceAttributeValue.objects.filter(
                listing_price_id=OuterRef("pk")
            )
        )
    )


def is_window_price_applicable(
    valid_from: datetime.datetime | None,
    valid_to: datetime.datetime | None,
    has_buyer_conditions: bool,
    now: datetime.datetime,
) -> bool:
    """Return whether a row's price belongs in the stored price of its listing.

    Only rows without buyer conditions apply to everyone, and only while their
    validity window is open.
    """
    if has_buyer_conditions:
        return False
    if valid_from is not None and now < valid_from:
        return False
    if valid_to is not None and now >= valid_to:
        return False
    return True


def find_window_price_rows_to_toggle(now: datetime.datetime, limit: int) -> list[int]:
    """Return ids of rows whose validity window opened or closed, lowest ids first.

    A row is returned when its window is open but it is not applied yet, or when
    it is applied but its window has ended. Each query is served by one of the
    partial indexes on the rows, so the check stays cheap on a large table.
    Rows without a window and edits that add buyer conditions or move the start
    of the window are the responsibility of the writers, which call
    `sync_window_price_rows` themselves.
    """
    rows_to_apply = _annotate_buyer_conditions(
        VariantChannelListingPrice.objects.filter(is_applied=False)
        .filter(Q(valid_from__isnull=False) | Q(valid_to__isnull=False))
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=now))
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gt=now))
    ).filter(has_buyer_conditions=False)
    rows_to_withdraw = VariantChannelListingPrice.objects.filter(
        is_applied=True, valid_to__lte=now
    )
    row_ids = set(rows_to_apply.order_by("pk").values_list("pk", flat=True)[:limit])
    row_ids.update(rows_to_withdraw.order_by("pk").values_list("pk", flat=True)[:limit])
    return sorted(row_ids)[:limit]


def mark_products_dirty_for_listings(listing_ids: Iterable[int]) -> set[int]:
    """Mark the products of the variant listings for a discounted price refresh.

    Return the ids of the variant listings whose product channel listing this
    call turned from clean to dirty. A listing that was already dirty may be in
    the middle of a refresh that has already read the old prices, so the caller
    cannot rely on that refresh to pick up a change made now.
    """
    listing_ids = list(listing_ids)
    if not listing_ids:
        return set()
    product_channel_by_listing_id: dict[int, tuple[int, int]] = {
        listing_id: (product_id, channel_id)
        for listing_id, product_id, channel_id in (
            ProductVariantChannelListing.objects.filter(pk__in=listing_ids).values_list(
                "pk", "variant__product_id", "channel_id"
            )
        )
    }
    wanted_pairs = set(product_channel_by_listing_id.values())
    with transaction.atomic():
        clean_listings = (
            ProductChannelListing.objects.select_for_update(of=("self",))
            .filter(
                product_id__in={product_id for product_id, _ in wanted_pairs},
                channel_id__in={channel_id for _, channel_id in wanted_pairs},
                discounted_price_dirty=False,
            )
            .order_by("pk")
            .values_list("pk", "product_id", "channel_id")
        )
        marked_pairs = set()
        marked_ids = []
        for product_channel_listing_id, product_id, channel_id in clean_listings:
            if (product_id, channel_id) in wanted_pairs:
                marked_pairs.add((product_id, channel_id))
                marked_ids.append(product_channel_listing_id)
        if marked_ids:
            ProductChannelListing.objects.filter(pk__in=marked_ids).update(
                discounted_price_dirty=True
            )
    return {
        listing_id
        for listing_id, pair in product_channel_by_listing_id.items()
        if pair in marked_pairs
    }


def sync_window_price_rows(row_ids: Iterable[int], now: datetime.datetime) -> None:
    """Make the stored listing prices follow the rows.

    The products of all the rows are marked for a discounted price refresh, so a
    changed price reaches the stored value even when the applied flag does not
    change. The flag of a row is set to match the current time only when the
    mark turned its product listing from clean to dirty, because only then is
    the refresh that will store the change guaranteed to run after this call. A
    row whose listing was already dirty keeps its flag and is picked up again by
    the next run of the toggle task.
    """
    row_ids = list(row_ids)
    if not row_ids:
        return
    with transaction.atomic():
        rows = list(
            _annotate_buyer_conditions(
                variant_channel_listing_price_qs_select_for_update().filter(
                    pk__in=row_ids
                )
            ).values_list(
                "pk",
                "variant_channel_listing_id",
                "valid_from",
                "valid_to",
                "has_buyer_conditions",
                "is_applied",
            )
        )
        marked_listing_ids = mark_products_dirty_for_listings(
            {listing_id for _, listing_id, _, _, _, _ in rows}
        )
        row_ids_to_apply = []
        row_ids_to_withdraw = []
        for (
            row_id,
            listing_id,
            valid_from,
            valid_to,
            has_buyer_conditions,
            is_applied,
        ) in rows:
            if listing_id not in marked_listing_ids:
                continue
            applicable = is_window_price_applicable(
                valid_from, valid_to, has_buyer_conditions, now
            )
            if applicable and not is_applied:
                row_ids_to_apply.append(row_id)
            elif is_applied and not applicable:
                row_ids_to_withdraw.append(row_id)
        if row_ids_to_apply:
            VariantChannelListingPrice.objects.filter(pk__in=row_ids_to_apply).update(
                is_applied=True
            )
        if row_ids_to_withdraw:
            VariantChannelListingPrice.objects.filter(
                pk__in=row_ids_to_withdraw
            ).update(is_applied=False)
