from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..order.models import FulfillmentLine, OrderLine
    from ..product.models import ProductVariant


class GiftCardEvents:
    """The different gift card event types."""

    ISSUED = "issued"
    BOUGHT = "bought"
    UPDATED = "updated"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    BALANCE_RESET = "balance_reset"
    EXPIRY_DATE_UPDATED = "expiry_date_updated"
    TAGS_UPDATED = "tags_updated"
    SENT_TO_CUSTOMER = "sent_to_customer"
    RESENT = "resent"
    NOTE_ADDED = "note_added"
    USED_IN_ORDER = "used_in_order"

    CHOICES = [
        (ISSUED, "The gift card was created be staff user or app."),
        (BOUGHT, "The gift card was bought by customer."),
        (UPDATED, "The gift card was updated."),
        (ACTIVATED, "The gift card was activated."),
        (DEACTIVATED, "The gift card was deactivated."),
        (BALANCE_RESET, "The gift card balance was reset."),
        (EXPIRY_DATE_UPDATED, "The gift card expiry date was updated."),
        (TAGS_UPDATED, "The gift card tags were updated."),
        (SENT_TO_CUSTOMER, "The gift card was sent to the customer."),
        (RESENT, "The gift card was resent to the customer."),
        (NOTE_ADDED, "A note was added to the gift card."),
        (USED_IN_ORDER, "The gift card was used in order."),
    ]


@dataclass
class GiftCardLineData:
    quantity: int
    order_line: "OrderLine"
    variant: Optional["ProductVariant"]
    fulfillment_line: "FulfillmentLine"
