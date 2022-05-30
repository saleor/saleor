from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import FulfillmentLine


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


class OrderOrigin:
    CHECKOUT = "checkout"  # order created from checkout
    DRAFT = "draft"  # order created from draft order
    REISSUE = "reissue"  # order created from reissue existing one

    CHOICES = [
        (CHECKOUT, "Checkout"),
        (DRAFT, "Draft"),
        (REISSUE, "Reissue"),
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
    WAITING_FOR_APPROVAL = (
        "waiting_for_approval"  # group of products waiting for approval
    )

    CHOICES = [
        (FULFILLED, "Fulfilled"),
        (REFUNDED, "Refunded"),
        (RETURNED, "Returned"),
        (REPLACED, "Replaced"),
        (REFUNDED_AND_RETURNED, "Refunded and returned"),
        (CANCELED, "Canceled"),
        (WAITING_FOR_APPROVAL, "Waiting for approval"),
    ]


class OrderEvents:
    """The different order event types."""

    CONFIRMED = "confirmed"
    DRAFT_CREATED = "draft_created"
    DRAFT_CREATED_FROM_REPLACE = "draft_created_from_replace"

    ADDED_PRODUCTS = "added_products"
    REMOVED_PRODUCTS = "removed_products"

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

    ORDER_LINE_PRODUCT_DELETED = "order_line_product_deleted"
    ORDER_LINE_VARIANT_DELETED = "order_line_variant_deleted"

    UPDATED_ADDRESS = "updated_address"

    EMAIL_SENT = "email_sent"

    PAYMENT_AUTHORIZED = "payment_authorized"
    PAYMENT_CAPTURED = "payment_captured"
    PAYMENT_REFUNDED = "payment_refunded"
    PAYMENT_VOIDED = "payment_voided"
    PAYMENT_FAILED = "payment_failed"

    TRANSACTION_EVENT = "transaction_event"
    TRANSACTION_CAPTURE_REQUESTED = "transaction_capture_requested"
    TRANSACTION_REFUND_REQUESTED = "transaction_refund_requested"
    TRANSACTION_VOID_REQUESTED = "transaction_void_requested"

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
    FULFILLMENT_AWAITS_APPROVAL = "fulfillment_awaits_approval"
    TRACKING_UPDATED = "tracking_updated"
    NOTE_ADDED = "note_added"

    # Used mostly for importing legacy data from before Enum-based events
    OTHER = "other"

    CHOICES = [
        (DRAFT_CREATED, "The draft order was created"),
        (DRAFT_CREATED_FROM_REPLACE, "The draft order with replace lines was created"),
        (ADDED_PRODUCTS, "Some products were added to the order"),
        (REMOVED_PRODUCTS, "Some products were removed from the order"),
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
        (ORDER_LINE_PRODUCT_DELETED, "The order line product was removed."),
        (ORDER_LINE_VARIANT_DELETED, "The order line product variant was removed."),
        (UPDATED_ADDRESS, "The address from the placed order was updated"),
        (EMAIL_SENT, "The email was sent"),
        (CONFIRMED, "Order was confirmed"),
        (PAYMENT_AUTHORIZED, "The payment was authorized"),
        (PAYMENT_CAPTURED, "The payment was captured"),
        (EXTERNAL_SERVICE_NOTIFICATION, "Notification from external service"),
        (PAYMENT_REFUNDED, "The payment was refunded"),
        (PAYMENT_VOIDED, "The payment was voided"),
        (PAYMENT_FAILED, "The payment was failed"),
        (TRANSACTION_EVENT, "The transaction event"),
        (TRANSACTION_CAPTURE_REQUESTED, "The capture on transaction requested"),
        (TRANSACTION_REFUND_REQUESTED, "The refund on transaction requested"),
        (TRANSACTION_VOID_REQUESTED, "The void on transaction requested"),
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
        (FULFILLMENT_AWAITS_APPROVAL, "Fulfillments awaits approval"),
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


class OrderAuthorizeStatus:
    """Determine a current authorize status for order.

    We treat the order as fully authorized when the sum of authorized and charged funds
    cover the order.total.
    We treat the order as partially authorized when the sum of authorized and charged
    funds covers only part of the order.total
    We treat the order as not authorized when the sum of authorized and charged funds is
    0.

    NONE - the funds are not authorized
    PARTIAL - the funds that are authorized or charged don't cover fully the order's
    total
    FULL - the funds that are authorized or charged fully cover the order's total
    """

    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"

    CHOICES = [
        (NONE, "The funds are not authorized"),
        (
            PARTIAL,
            "The funds that are authorized or charged don't cover fully the order's "
            "total",
        ),
        (
            FULL,
            "The funds that are authorized or charged fully cover the order's total",
        ),
    ]


class OrderChargeStatus:
    """Determine the current charge status for the order.

    We treat the order as overcharged when the charged amount is bigger that order.total
    We treat the order as fully charged when the charged amount is equal to order.total.
    We treat the order as partially charged when the charged amount covers only part of
    the order.total

    NONE - the funds are not charged.
    PARTIAL - the funds that are charged don't cover the order's total
    FULL - the funds that are charged fully cover the order's total
    OVERCHARGED - the charged funds are bigger than order's total
    """

    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    OVERCHARGED = "overcharged"

    CHOICES = [
        (NONE, "The funds are not charged."),
        (PARTIAL, "The funds that are charged, don't cover the order's total"),
        (FULL, "The funds that are charged fully cover the order's total"),
        (OVERCHARGED, "The charged funds are bigger than order's total"),
    ]


@dataclass
class FulfillmentLineData:
    line: "FulfillmentLine"
    quantity: int
    replace: bool = False
