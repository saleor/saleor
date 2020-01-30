class OrderStatus:
    DRAFT = "draft"  # fully editable, not confirmed order created by staff users
    UNFULFILLED = "unfulfilled"  # order with no items marked as fulfilled
    PARTIALLY_FULFILLED = (
        "partially fulfilled"  # order with some items marked as fulfilled
    )
    FULFILLED = "fulfilled"  # order with all items marked as fulfilled
    CANCELED = "canceled"  # permanently canceled order

    CHOICES = [
        (DRAFT, "Draft"),
        (UNFULFILLED, "Unfulfilled"),
        (PARTIALLY_FULFILLED, "Partially fulfilled"),
        (FULFILLED, "Fulfilled"),
        (CANCELED, "Canceled"),
    ]


class FulfillmentStatus:
    FULFILLED = "fulfilled"  # group of products in an order marked as fulfilled
    CANCELED = "canceled"  # fulfilled group of products in an order marked as canceled

    CHOICES = [
        (FULFILLED, "Fulfilled"),
        (CANCELED, "Canceled"),
    ]


class OrderEvents:
    """The different order event types."""

    DRAFT_CREATED = "draft_created"
    DRAFT_ADDED_PRODUCTS = "draft_added_products"
    DRAFT_REMOVED_PRODUCTS = "draft_removed_products"

    PLACED = "placed"
    PLACED_FROM_DRAFT = "placed_from_draft"

    OVERSOLD_ITEMS = "oversold_items"
    CANCELED = "canceled"

    ORDER_MARKED_AS_PAID = "order_marked_as_paid"
    ORDER_FULLY_PAID = "order_fully_paid"

    UPDATED_ADDRESS = "updated_address"

    EMAIL_SENT = "email_sent"

    PAYMENT_CAPTURED = "payment_captured"
    PAYMENT_REFUNDED = "payment_refunded"
    PAYMENT_VOIDED = "payment_voided"
    PAYMENT_FAILED = "payment_failed"

    FULFILLMENT_CANCELED = "fulfillment_canceled"
    FULFILLMENT_RESTOCKED_ITEMS = "fulfillment_restocked_items"
    FULFILLMENT_FULFILLED_ITEMS = "fulfillment_fulfilled_items"
    TRACKING_UPDATED = "tracking_updated"
    NOTE_ADDED = "note_added"

    # Used mostly for importing legacy data from before Enum-based events
    OTHER = "other"

    CHOICES = [
        (DRAFT_CREATED, "The draft order was created"),
        (DRAFT_ADDED_PRODUCTS, "Some products were added to the draft order"),
        (DRAFT_REMOVED_PRODUCTS, "Some products were removed from the draft order"),
        (PLACED, "The order was placed"),
        (PLACED_FROM_DRAFT, "The draft order was placed"),
        (OVERSOLD_ITEMS, "The draft order was placed with oversold items"),
        (CANCELED, "The order was canceled"),
        (ORDER_MARKED_AS_PAID, "The order was manually marked as fully paid"),
        (ORDER_FULLY_PAID, "The order was fully paid"),
        (UPDATED_ADDRESS, "The address from the placed order was updated"),
        (EMAIL_SENT, "The email was sent"),
        (PAYMENT_CAPTURED, "The payment was captured"),
        (PAYMENT_REFUNDED, "The payment was refunded"),
        (PAYMENT_VOIDED, "The payment was voided"),
        (PAYMENT_FAILED, "The payment was failed"),
        (FULFILLMENT_CANCELED, "A fulfillment was canceled"),
        (FULFILLMENT_RESTOCKED_ITEMS, "The items of the fulfillment were restocked"),
        (FULFILLMENT_FULFILLED_ITEMS, "Some items were fulfilled"),
        (TRACKING_UPDATED, "The fulfillment's tracking code was updated"),
        (NOTE_ADDED, "A note was added to the order"),
        (OTHER, "An unknown order event containing a message"),
    ]


class OrderEventsEmails:
    """The different order emails event types."""

    PAYMENT = "payment_confirmation"
    SHIPPING = "shipping_confirmation"
    TRACKING_UPDATED = "tracking_updated"
    ORDER = "order_confirmation"
    FULFILLMENT = "fulfillment_confirmation"
    DIGITAL_LINKS = "digital_links"

    CHOICES = [
        (PAYMENT, "The payment confirmation email was sent"),
        (SHIPPING, "The shipping confirmation email was sent"),
        (TRACKING_UPDATED, "The fulfillment tracking code email was sent"),
        (ORDER, "The order placement confirmation email was sent"),
        (FULFILLMENT, "The fulfillment confirmation email was sent"),
        (DIGITAL_LINKS, "The email containing the digital links was sent"),
    ]
