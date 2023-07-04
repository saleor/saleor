from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Union

from ..graphql.channel import ChannelContext
from ..product.models import ProductVariant
from ..warehouse.models import Stock
from .fetch import CheckoutLineInfo
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


def get_insufficient_stock_lines(
    lines_with_stock: Iterable[Tuple["CheckoutLineInfo", list["Stock"]]]
) -> list[Tuple["CheckoutLineInfo", int]]:
    """Return checkout lines with insufficient stock."""
    variant_to_quantity_map: dict[int, int] = defaultdict(int)
    variant_to_available_quantity_map: dict[int, int] = defaultdict(int)
    for line_info, variant_stocks in lines_with_stock:
        variant_to_quantity_map[line_info.variant.id] += line_info.line.quantity
        variant_to_available_quantity_map[line_info.variant.id] = sum(
            [
                stock.available_quantity  # type: ignore[attr-defined]
                for stock in variant_stocks
            ]
        )
    insufficient_stocks = []
    for line_info, variant_stocks in lines_with_stock:
        if not line_info.variant.track_inventory:
            continue
        quantity = variant_to_quantity_map[line_info.variant.id]
        available_quantity = variant_to_available_quantity_map[line_info.variant.id]
        if available_quantity < quantity:
            insufficient_stocks.append((line_info, available_quantity))
    return insufficient_stocks


CHECKOUT_LINE_PK_TYPE = str


def get_checkout_lines_problems(
    lines_with_stock: Iterable[Tuple["CheckoutLineInfo", list["Stock"]]]
) -> dict[CHECKOUT_LINE_PK_TYPE, list[CHECKOUT_LINE_PROBLEM_TYPE]]:
    """Return a list of all problems with the checkout lines.

    It accepts the checkout lines infos and the list of the stocks available for the
    lines. It returns a list of the problems with the checkout lines.

    The stocks need to have annotated available_quantity field.
    """
    problems: dict[
        CHECKOUT_LINE_PK_TYPE, list[CHECKOUT_LINE_PROBLEM_TYPE]
    ] = defaultdict(list)
    insufficient_stock = get_insufficient_stock_lines(lines_with_stock)
    if insufficient_stock:
        for line_info, available_quantity in insufficient_stock:
            problems[str(line_info.line.pk)].append(
                CheckoutLineProblemInsufficientStock(
                    available_quantity=available_quantity,
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
