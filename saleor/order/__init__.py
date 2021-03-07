from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..product.models import ProductVariant
    from .models import FulfillmentLine, OrderLine


class OrderStatus:
    DRAFT = "draft"  # fully editable, not finalized order created by staff users
    UNCONFIRMED = (
        "unconfirmed"  # order created by customers when confirmation is required
    )
    UNFULFILLED = "unfulfilled"  # order with no items marked as fulfilled
    PARTIALLY_FULFILLED = (
        "partially fulfilled"  # order with some items marked as fulfilled
    )
    FULFILLED = "fulfilled"  # order with all items marked as fulfilled

    PARTIALLY_RETURNED = (
        "partially_returned"  # order with some items marked as returned
    )
    RETURNED = "returned"  # order with all items marked as returned
    CANCELED = "canceled"  # permanently canceled order

    CHOICES = [
        (DRAFT, "Draft"),
        (UNCONFIRMED, "Unconfirmed"),
        (UNFULFILLED, "Unfulfilled"),
        (PARTIALLY_FULFILLED, "Partially fulfilled"),
        (PARTIALLY_RETURNED, "Partially returned"),
        (RETURNED, "Returned"),
        (FULFILLED, "Fulfilled"),
        (CANCELED, "Canceled"),
    ]


class FulfillmentStatus:
    FULFILLED = "fulfilled"  # group of products in an order marked as fulfilled
    REFUNDED = "refunded"  # group of refunded products
    RETURNED = "returned"  # group of returned products
    REFUNDED_AND_RETURNED = (
        "refunded_and_returned"  # group of returned and replaced products
    )
    REPLACED = "replaced"  # group of replaced products
    CANCELED = "canceled"  # fulfilled group of products in an order marked as canceled

    CHOICES = [
        (FULFILLED, "Fulfilled"),
        (REFUNDED, "Refunded"),
        (RETURNED, "Returned"),
        (REPLACED, "Replaced"),
        (REFUNDED_AND_RETURNED, "Refunded and returned"),
        (CANCELED, "Canceled"),
    ]


class OrderEvents:
    """The different order event types."""

    CONFIRMED = "confirmed"
    DRAFT_CREATED = "draft_created"
    DRAFT_CREATED_FROM_REPLACE = "draft_created_from_replace"

    DRAFT_ADDED_PRODUCTS = "draft_added_products"
    DRAFT_REMOVED_PRODUCTS = "draft_removed_products"

    PLACED = "placed"
    PLACED_FROM_DRAFT = "placed_from_draft"

    OVERSOLD_ITEMS = "oversold_items"
    CANCELED = "canceled"

    ORDER_MARKED_AS_PAID = "order_marked_as_paid"
    ORDER_FULLY_PAID = "order_fully_paid"
    ORDER_REPLACEMENT_CREATED = "order_replacement_created"

    ORDER_DISCOUNT_ADDED = "order_discount_added"
    ORDER_DISCOUNT_AUTOMATICALLY_UPDATED = "order_discount_automatically_updated"
    ORDER_DISCOUNT_UPDATED = "order_discount_updated"
    ORDER_DISCOUNT_DELETED = "order_discount_deleted"
    ORDER_LINE_DISCOUNT_UPDATED = "order_line_discount_updated"
    ORDER_LINE_DISCOUNT_REMOVED = "order_line_discount_removed"

    UPDATED_ADDRESS = "updated_address"

    EMAIL_SENT = "email_sent"

    PAYMENT_AUTHORIZED = "payment_authorized"
    PAYMENT_CAPTURED = "payment_captured"
    PAYMENT_REFUNDED = "payment_refunded"
    PAYMENT_VOIDED = "payment_voided"
    PAYMENT_FAILED = "payment_failed"
    EXTERNAL_SERVICE_NOTIFICATION = "external_service_notification"

    INVOICE_REQUESTED = "invoice_requested"
    INVOICE_GENERATED = "invoice_generated"
    INVOICE_UPDATED = "invoice_updated"
    INVOICE_SENT = "invoice_sent"

    FULFILLMENT_CANCELED = "fulfillment_canceled"
    FULFILLMENT_RESTOCKED_ITEMS = "fulfillment_restocked_items"
    FULFILLMENT_FULFILLED_ITEMS = "fulfillment_fulfilled_items"
    FULFILLMENT_REFUNDED = "fulfillment_refunded"
    FULFILLMENT_RETURNED = "fulfillment_returned"
    FULFILLMENT_REPLACED = "fulfillment_replaced"
    TRACKING_UPDATED = "tracking_updated"
    NOTE_ADDED = "note_added"

    # Used mostly for importing legacy data from before Enum-based events
    OTHER = "other"

    CHOICES = [
        (DRAFT_CREATED, "The draft order was created"),
        (DRAFT_CREATED_FROM_REPLACE, "The draft order with replace lines was created"),
        (DRAFT_ADDED_PRODUCTS, "Some products were added to the draft order"),
        (DRAFT_REMOVED_PRODUCTS, "Some products were removed from the draft order"),
        (PLACED, "The order was placed"),
        (PLACED_FROM_DRAFT, "The draft order was placed"),
        (OVERSOLD_ITEMS, "The draft order was placed with oversold items"),
        (CANCELED, "The order was canceled"),
        (ORDER_MARKED_AS_PAID, "The order was manually marked as fully paid"),
        (ORDER_FULLY_PAID, "The order was fully paid"),
        (ORDER_REPLACEMENT_CREATED, "The draft order was created based on this order."),
        (ORDER_DISCOUNT_ADDED, "New order discount applied to this order."),
        (
            ORDER_DISCOUNT_AUTOMATICALLY_UPDATED,
            "Order discount was automatically updated after the changes in order.",
        ),
        (ORDER_DISCOUNT_UPDATED, "Order discount was updated for this order."),
        (ORDER_DISCOUNT_DELETED, "Order discount was deleted for this order."),
        (ORDER_LINE_DISCOUNT_UPDATED, "Order line was discounted."),
        (ORDER_LINE_DISCOUNT_REMOVED, "The discount for order line was removed."),
        (UPDATED_ADDRESS, "The address from the placed order was updated"),
        (EMAIL_SENT, "The email was sent"),
        (CONFIRMED, "Order was confirmed"),
        (PAYMENT_AUTHORIZED, "The payment was authorized"),
        (PAYMENT_CAPTURED, "The payment was captured"),
        (EXTERNAL_SERVICE_NOTIFICATION, "Notification from external service"),
        (PAYMENT_REFUNDED, "The payment was refunded"),
        (PAYMENT_VOIDED, "The payment was voided"),
        (PAYMENT_FAILED, "The payment was failed"),
        (INVOICE_REQUESTED, "An invoice was requested"),
        (INVOICE_GENERATED, "An invoice was generated"),
        (INVOICE_UPDATED, "An invoice was updated"),
        (INVOICE_SENT, "An invoice was sent"),
        (FULFILLMENT_CANCELED, "A fulfillment was canceled"),
        (FULFILLMENT_RESTOCKED_ITEMS, "The items of the fulfillment were restocked"),
        (FULFILLMENT_FULFILLED_ITEMS, "Some items were fulfilled"),
        (FULFILLMENT_REFUNDED, "Some items were refunded"),
        (FULFILLMENT_RETURNED, "Some items were returned"),
        (FULFILLMENT_REPLACED, "Some items were replaced"),
        (TRACKING_UPDATED, "The fulfillment's tracking code was updated"),
        (NOTE_ADDED, "A note was added to the order"),
        (OTHER, "An unknown order event containing a message"),
    ]


class OrderEventsEmails:
    """The different order emails event types."""

    CONFIRMED = "confirmed"
    PAYMENT = "payment_confirmation"
    SHIPPING = "shipping_confirmation"
    TRACKING_UPDATED = "tracking_updated"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_CANCEL = "order_cancel"
    ORDER_REFUND = "order_refund"
    FULFILLMENT = "fulfillment_confirmation"
    DIGITAL_LINKS = "digital_links"

    CHOICES = [
        (PAYMENT, "The payment confirmation email was sent"),
        (CONFIRMED, "The order confirmed email was sent"),
        (SHIPPING, "The shipping confirmation email was sent"),
        (TRACKING_UPDATED, "The fulfillment tracking code email was sent"),
        (ORDER_CONFIRMATION, "The order placement confirmation email was sent"),
        (ORDER_CANCEL, "The order cancel confirmation email was sent"),
        (ORDER_REFUND, "The order refund confirmation email was sent"),
        (FULFILLMENT, "The fulfillment confirmation email was sent"),
        (DIGITAL_LINKS, "The email containing the digital links was sent"),
    ]


@dataclass
class OrderLineData:
    line: "OrderLine"
    quantity: int
    variant: Optional["ProductVariant"] = None
    replace: bool = False
    warehouse_pk: Optional[str] = None


@dataclass
class FulfillmentLineData:
    line: "FulfillmentLine"
    quantity: int
    replace: bool = False
