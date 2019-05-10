from django.utils.translation import pgettext_lazy


class CustomerEvents:
    """The different customer event types."""

    # Order related events
    PLACED_ORDER = "placed_order"  # created an order
    NOTE_ADDED_TO_ORDER = "note_added_to_order"  # added a note to one of their orders
    DIGITAL_LINK_DOWNLOADED = "digital_link_downloaded"  # downloaded a digital good

    # Staff actions over customers events
    CUSTOMER_DELETED = "customer_deleted"  # staff user deleted a customer

    CHOICES = [
        (
            PLACED_ORDER,
            pgettext_lazy(
                "Event from a customer that placed an order",
                "An order was placed",  # noqa
            ),
        ),
        (
            NOTE_ADDED_TO_ORDER,
            pgettext_lazy(
                "Event from a customer that added a note to one of their orders",
                "A note was added",
            ),
        ),
        (
            DIGITAL_LINK_DOWNLOADED,
            pgettext_lazy(
                "Event from a customer that downloaded an ordered digital good",
                "A digital good was downloaded",
            ),
        ),
        (
            CUSTOMER_DELETED,
            pgettext_lazy(
                "Event from a staff user that deleted a customer",
                "A customer was deleted",
            ),
        ),
    ]
