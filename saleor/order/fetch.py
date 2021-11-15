from typing import TYPE_CHECKING, Iterable, List, Optional

from . import OrderData, OrderLineData

if TYPE_CHECKING:
    from .models import Order


def fetch_order_info(
    order: "Order", order_lines_info: Optional[Iterable[OrderLineData]] = None
) -> OrderData:
    if not order_lines_info:
        order_lines_info = fetch_order_lines(order)
    order_data = OrderData(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=order.get_last_payment(),
        lines_data=order_lines_info,
    )
    return order_data


def fetch_order_lines(order: "Order") -> List[OrderLineData]:
    lines = order.lines.prefetch_related("variant__digital_content")
    lines_info = []
    for line in lines:
        is_digital = line.is_digital
        variant = line.variant
        lines_info.append(
            OrderLineData(
                line=line,
                quantity=line.quantity,
                is_digital=is_digital,
                variant=variant,
                digital_content=variant.digital_content
                if is_digital and variant
                else None,
            )
        )

    return lines_info
