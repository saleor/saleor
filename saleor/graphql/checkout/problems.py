from collections import defaultdict
from typing import Iterable, Tuple

from ...checkout.fetch import CheckoutLineInfo
from ...warehouse.models import Stock
from .enums import CheckoutLineProblemCode, CheckoutProblemCode


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
CHECKOUT_LINE_PROBLEM_TYPE = dict[str, str]


def get_checkout_lines_problems(
    lines_with_stock: Iterable[Tuple["CheckoutLineInfo", list["Stock"]]]
) -> dict[CHECKOUT_LINE_PK_TYPE, list[CHECKOUT_LINE_PROBLEM_TYPE]]:
    """Return a list of all problems with the checkout lines.

    It accepts the checkout lines infos and the list of the stocks available for the
    lines. It returns a list of the problems with the checkout lines.

    The stocks need to have annotated available_quantity field.
    """
    problems = defaultdict(list)
    insufficient_stock = get_insufficient_stock_lines(lines_with_stock)
    if insufficient_stock:
        for line_info, available_quantity in insufficient_stock:
            problems[str(line_info.line.pk)].append(
                {
                    "code": CheckoutLineProblemCode.INSUFFICIENT_STOCK.value,
                    "message": (
                        f"Insufficient stock. Only {max(available_quantity, 0)} "
                        "remaining in stock."
                    ),
                    "field": "quantity",
                }
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
    out_of_stock_problem = False
    for line_problems in checkout_lines_problem.values():
        if any(
            [
                problem["code"] == CheckoutLineProblemCode.INSUFFICIENT_STOCK.value
                for problem in line_problems
            ]
        ):
            out_of_stock_problem = True

    if out_of_stock_problem:
        problems.append(
            {
                "code": CheckoutProblemCode.INSUFFICIENT_STOCK.value,
                "message": "Insufficient stock for some variants in checkout.",
                "field": "lines",
            }
        )
    return problems
