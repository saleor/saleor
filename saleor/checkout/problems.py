import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Union

import pytz

from ..graphql.channel import ChannelContext
from ..product.models import ProductChannelListing, ProductVariant
from ..warehouse.models import Stock
from .fetch import CheckoutInfo, CheckoutLineInfo
from .models import CheckoutLine


@dataclass
class CheckoutLineProblemInsufficientStock:
    available_quantity: int
    line: CheckoutLine
    variant: Optional[ChannelContext[ProductVariant]] = None


@dataclass
class CheckoutLineProblemVariantNotAvailable:
    line: CheckoutLine


CHECKOUT_LINE_PROBLEM_TYPE = Union[
    CheckoutLineProblemInsufficientStock, CheckoutLineProblemVariantNotAvailable
]
CHECKOUT_PROBLEM_TYPE = Union[
    CheckoutLineProblemInsufficientStock, CheckoutLineProblemVariantNotAvailable
]

VARIANT_ID = int
PRODUCT_ID = int
CHANNEL_SLUG = str
COUNTRY_CODE = str

CHECKOUT_LINE_PK_TYPE = str


def get_insufficient_stock_lines(
    lines: Iterable["CheckoutLineInfo"],
    variant_stock_map: dict[
        tuple[
            VARIANT_ID,
            CHANNEL_SLUG,
            COUNTRY_CODE,
        ],
        Iterable[Stock],
    ],
    country_code: str,
) -> list[Tuple["CheckoutLineInfo", int]]:
    """Return checkout lines with insufficient stock."""
    variant_to_quantity_map: dict[int, int] = defaultdict(int)
    variant_to_available_quantity_map: dict[int, int] = defaultdict(int)
    for line_info in lines:
        variant_to_quantity_map[line_info.variant.id] += line_info.line.quantity
        variant_stocks = variant_stock_map.get(
            (line_info.variant.id, line_info.channel.slug, country_code), []
        )
        variant_to_available_quantity_map[line_info.variant.id] = sum(
            [
                stock.available_quantity  # type: ignore[attr-defined]
                for stock in variant_stocks
            ]
        )
    insufficient_stocks = []
    for line_info in lines:
        if not line_info.variant.track_inventory:
            continue
        quantity = variant_to_quantity_map[line_info.variant.id]
        available_quantity = variant_to_available_quantity_map[line_info.variant.id]
        if available_quantity < quantity:
            insufficient_stocks.append((line_info, available_quantity))
    return insufficient_stocks


def line_is_not_available(
    line: "CheckoutLineInfo",
    now: datetime.datetime,
    product_channel_listings_map: dict[
        tuple[
            PRODUCT_ID,
            CHANNEL_SLUG,
        ],
        ProductChannelListing,
    ],
) -> bool:
    product_channel_listing = product_channel_listings_map.get(
        (line.product.id, line.channel.slug), None
    )
    if not product_channel_listing:
        return True

    available_at = product_channel_listing.available_for_purchase_at
    if available_at is not None and available_at > now:
        return True

    if product_channel_listing.is_published is False:
        return True

    if not line.channel_listing:
        return True

    if line.channel_listing.price_amount is None:
        return True

    return False


def get_not_available_lines(
    lines: Iterable["CheckoutLineInfo"],
    product_channel_listings_map: dict[
        tuple[
            PRODUCT_ID,
            CHANNEL_SLUG,
        ],
        ProductChannelListing,
    ],
):
    lines_not_available = []
    now = datetime.datetime.now(pytz.UTC)
    for line in lines:
        if line_is_not_available(line, now, product_channel_listings_map):
            lines_not_available.append(line)

    return lines_not_available


def get_checkout_lines_problems(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    variant_stock_map: dict[
        tuple[
            VARIANT_ID,
            CHANNEL_SLUG,
            COUNTRY_CODE,
        ],
        Iterable[Stock],
    ],
    product_channel_listings_map: dict[
        tuple[
            PRODUCT_ID,
            CHANNEL_SLUG,
        ],
        ProductChannelListing,
    ],
) -> dict[CHECKOUT_LINE_PK_TYPE, list[CHECKOUT_LINE_PROBLEM_TYPE]]:
    """Return a list of all problems with the checkout lines.

    The stocks need to have annotated available_quantity field.
    """
    problems: dict[
        CHECKOUT_LINE_PK_TYPE, list[CHECKOUT_LINE_PROBLEM_TYPE]
    ] = defaultdict(list)

    not_available_lines = get_not_available_lines(lines, product_channel_listings_map)
    if not_available_lines:
        for line in not_available_lines:
            problems[str(line.line.pk)].append(
                CheckoutLineProblemVariantNotAvailable(line=line.line)
            )
    lines = [line for line in lines if line not in not_available_lines]

    insufficient_stock = get_insufficient_stock_lines(
        lines, variant_stock_map, checkout_info.checkout.country.code
    )
    if insufficient_stock:
        for line_info, available_quantity in insufficient_stock:
            problems[str(line_info.line.pk)].append(
                CheckoutLineProblemInsufficientStock(
                    available_quantity=max(available_quantity, 0),
                    line=line_info.line,
                    variant=ChannelContext(
                        node=line_info.variant, channel_slug=line_info.channel.slug
                    ),
                )
            )
    return problems


def get_checkout_problems(
    checkout_lines_problem: dict[
        CHECKOUT_LINE_PK_TYPE, list[CHECKOUT_LINE_PROBLEM_TYPE]
    ]
):
    """Return a list of all problems with the checkout.

    It accepts the list of the checkout line info with the list of the stocks available
    for the given line. It returns a list of the problems with the checkout.

    The stocks need to have annotated available_quantity field.
    """
    problems = []
    for line_problems in checkout_lines_problem.values():
        problems.extend(line_problems)
    return problems
