from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional
from uuid import UUID

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..payment.models import Payment
    from ..product.models import DigitalContent, ProductVariant
    from .models import Order, OrderLine


@dataclass
class OrderInfo:
    order: "Order"
    customer_email: "str"
    channel: "Channel"
    payment: Optional["Payment"]
    lines_data: Iterable["OrderLineInfo"]


@dataclass
class OrderLineInfo:
    line: "OrderLine"
    quantity: int
    variant: Optional["ProductVariant"] = None
    is_digital: Optional[bool] = None
    digital_content: Optional["DigitalContent"] = None
    replace: bool = False
    warehouse_pk: Optional[UUID] = None


def fetch_order_info(order: "Order") -> OrderInfo:
    order_lines_info = fetch_order_lines(order)
    order_data = OrderInfo(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=order.get_last_payment(),
        lines_data=order_lines_info,
    )
    return order_data


def fetch_order_lines(order: "Order") -> List[OrderLineInfo]:
    lines = order.lines.prefetch_related("variant__digital_content")
    lines_info = []
    for line in lines:
        is_digital = line.is_digital
        variant = line.variant
        lines_info.append(
            OrderLineInfo(
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
