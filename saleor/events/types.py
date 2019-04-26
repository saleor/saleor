from enum import Enum


class OrderEvents(Enum):
    DRAFT_CREATED = 'draft_created'
    DRAFT_SELECTED_SHIPPING_METHOD = 'draft_selected_shipping_method'  # FIXME
    DRAFT_ADDED_PRODUCTS = 'draft_added_products'      # FIXME: IMPLEMENT ME
    DRAFT_REMOVED_PRODUCTS = 'draft_removed_products'  # FIXME: IMPLEMENT ME

    PLACED = 'placed'
    PLACED_FROM_DRAFT = 'draft_placed'

    OVERSOLD_ITEMS = 'oversold_items'
    CANCELED = 'canceled'

    ORDER_MARKED_AS_PAID = 'marked_as_paid'
    ORDER_FULLY_PAID = 'order_paid'

    UPDATED = 'updated'
    UPDATED_ADDRESS = 'updated_address'

    EMAIL_SENT = 'email_sent'

    PAYMENT_CAPTURED = 'captured'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_VOIDED = 'voided'
    PAYMENT_FAILED = 'payment_failed'  # FIXME: IMPLEMENT ME

    FULFILLMENT_CANCELED = 'fulfillment_canceled'
    FULFILLMENT_RESTOCKED_ITEMS = 'restocked_items'
    FULFILLMENT_FULFILLED_ITEMS = 'fulfilled_items'
    TRACKING_UPDATED = 'tracking_updated'
    NOTE_ADDED = 'note_added'

    # Used mostly for importing legacy data from before Enum-based events
    OTHER = 'other'


class OrderEventsEmails(Enum):
    PAYMENT = 'payment_confirmation'
    SHIPPING = 'shipping_confirmation'
    TRACKING_UPDATED = 'tracking_updated'
    ORDER = 'order_confirmation'
    FULFILLMENT = 'fulfillment_confirmation'
    DIGITAL_LINKS = 'digital_links'
