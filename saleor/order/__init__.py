from django.utils.translation import pgettext_lazy


class OrderStatus:
    DRAFT = "draft"
    UNFULFILLED = "unfulfilled"
    PARTIALLY_FULFILLED = "partially fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"

    CHOICES = [
        (
            DRAFT,
            pgettext_lazy(
                "Status for a fully editable, not confirmed order created by "
                "staff users",
                "Draft",
            ),
        ),
        (
            UNFULFILLED,
            pgettext_lazy(
                "Status for an order with no items marked as fulfilled", "Unfulfilled"
            ),
        ),
        (
            PARTIALLY_FULFILLED,
            pgettext_lazy(
                "Status for an order with some items marked as fulfilled",
                "Partially fulfilled",
            ),
        ),
        (
            FULFILLED,
            pgettext_lazy(
                "Status for an order with all items marked as fulfilled", "Fulfilled"
            ),
        ),
        (
            CANCELED,
            pgettext_lazy("Status for a permanently canceled order", "Canceled"),
        ),
    ]


class FulfillmentStatus:
    FULFILLED = "fulfilled"
    CANCELED = "canceled"

    CHOICES = [
        (
            FULFILLED,
            pgettext_lazy(
                "Status for a group of products in an order marked as fulfilled",
                "Fulfilled",
            ),
        ),
        (
            CANCELED,
            pgettext_lazy(
                "Status for a fulfilled group of products in an order marked "
                "as canceled",
                "Canceled",
            ),
        ),
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
        (
            DRAFT_CREATED,
            pgettext_lazy(
                "Event from a staff user that created a draft order",
                "The draft order was created",
            ),
        ),
        (
            DRAFT_ADDED_PRODUCTS,
            pgettext_lazy(
                "Event from a staff user that added products to a draft order",
                "Some products were added to the draft order",
            ),
        ),
        (
            DRAFT_REMOVED_PRODUCTS,
            pgettext_lazy(
                "Event from a staff user that removed products from a draft order",
                "Some products were removed from the draft order",
            ),
        ),
        (
            PLACED,
            pgettext_lazy(
                "Event from a user or anonymous user that placed their order",
                "The order was placed",
            ),
        ),
        (
            PLACED_FROM_DRAFT,
            pgettext_lazy(
                "Event from a staff user that placed a draft order",
                "The draft order was placed",
            ),
        ),
        (
            OVERSOLD_ITEMS,
            pgettext_lazy(
                "Event from a staff user that placed a draft order by passing "
                "oversold items",
                "The draft order was placed with oversold items",
            ),
        ),
        (
            CANCELED,
            pgettext_lazy(
                "Event from a staff user that canceled an order",
                "The order was canceled",
            ),
        ),
        (
            ORDER_MARKED_AS_PAID,
            pgettext_lazy(
                "Event from a staff user that manually marked an order as "
                "fully paid",
                "The order was manually marked as fully paid",
            ),
        ),
        (
            ORDER_FULLY_PAID,
            pgettext_lazy(
                "Event from a payment that made the order to be fully paid",
                "The order was fully paid",
            ),
        ),
        (
            UPDATED_ADDRESS,
            pgettext_lazy(
                "Event from a staff user that updated an address of a " "placed order",
                "The address from the placed order was updated",
            ),
        ),
        (
            EMAIL_SENT,
            pgettext_lazy(
                "Event generated from a user action that led to a " "email being sent",
                "The email was sent",
            ),
        ),
        (
            PAYMENT_CAPTURED,
            pgettext_lazy(
                "Event from a user payment that successfully captured a "
                "given amount of money",
                "The payment was captured",
            ),
        ),
        (
            PAYMENT_REFUNDED,
            pgettext_lazy(
                "Event from a staff user that successfully refunded a payment",
                "The payment was refunded",
            ),
        ),
        (
            PAYMENT_VOIDED,
            pgettext_lazy(
                "Event from a staff user that successfully voided an "
                "authorized payment",
                "The payment was voided",
            ),
        ),
        (
            PAYMENT_FAILED,
            pgettext_lazy(
                "Event from a user that generated an unsuccessful payment",
                "The payment was failed",
            ),
        ),
        (
            FULFILLMENT_CANCELED,
            pgettext_lazy(
                "Event from a staff user that canceled a fulfillment",
                "A fulfillment was canceled",
            ),
        ),
        (
            FULFILLMENT_RESTOCKED_ITEMS,
            pgettext_lazy(
                "Event from a staff user that restocked the items that were used "
                "for a fulfillment",
                "The items of the fulfillment were restocked",
            ),
        ),
        (
            FULFILLMENT_FULFILLED_ITEMS,
            pgettext_lazy(
                "Event from a staff user that fulfilled some items",
                "Some items were fulfilled",
            ),
        ),
        (
            TRACKING_UPDATED,
            pgettext_lazy(
                "Event from a staff user that updated the tracking code of an "
                "existing fulfillment",
                "The fulfillment's tracking code was updated",
            ),
        ),
        (
            NOTE_ADDED,
            pgettext_lazy(
                "Event from an user that added a note to an order",
                "A note was added to the order",
            ),
        ),
        (
            OTHER,
            pgettext_lazy(
                "An other type of order event containing a message",
                "An unknown order event containing a message",
            ),
        ),
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
        (
            PAYMENT,
            pgettext_lazy(
                "A payment confirmation email was sent",
                "The payment confirmation email was sent",
            ),
        ),
        (
            SHIPPING,
            pgettext_lazy(
                "A shipping confirmation email was sent",
                "The shipping confirmation email was sent",
            ),
        ),
        (
            TRACKING_UPDATED,
            pgettext_lazy(
                "A tracking code update confirmation email was sent",
                "The fulfillment tracking code email was sent",
            ),
        ),
        (
            ORDER,
            pgettext_lazy(
                "A order confirmation email was sent",
                "The order placement confirmation email was sent",
            ),
        ),
        (
            FULFILLMENT,
            pgettext_lazy(
                "A fulfillment confirmation email was sent",
                "The fulfillment confirmation email was sent",
            ),
        ),
        (
            DIGITAL_LINKS,
            pgettext_lazy(
                "An email containing a or some digital link was sent",
                "The email containing the digital links was sent",
            ),
        ),
    ]
