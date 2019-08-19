from django.utils.translation import pgettext_lazy


class CustomerEvents:
    """The different customer event types."""

    # Account related events
    ACCOUNT_CREATED = "account_created"
    PASSWORD_RESET_LINK_SENT = "password_reset_link_sent"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGE = "password_change"

    # Order related events
    PLACED_ORDER = "placed_order"  # created an order
    NOTE_ADDED_TO_ORDER = "note_added_to_order"  # added a note to one of their orders
    DIGITAL_LINK_DOWNLOADED = "digital_link_downloaded"  # downloaded a digital good

    # Staff actions over customers events
    CUSTOMER_DELETED = "customer_deleted"  # staff user deleted a customer
    EMAIL_ASSIGNED = "email_assigned"  # the staff user assigned a email to the customer
    NAME_ASSIGNED = "name_assigned"  # the staff user added set a name to the customer
    NOTE_ADDED = "note_added"  # the staff user added a note to the customer

    CHOICES = [
        (
            ACCOUNT_CREATED,
            pgettext_lazy(
                "Event from a customer that got their account created",
                "The account account was created",
            ),
        ),
        (
            PASSWORD_RESET_LINK_SENT,
            pgettext_lazy(
                "Event from a customer that got the password reset link sent by email",
                "Password reset link was sent to the customer",
            ),
        ),
        (
            PASSWORD_RESET,
            pgettext_lazy(
                "Event from a customer that reset their password",
                "The account password was reset",
            ),
        ),
        (
            PLACED_ORDER,
            pgettext_lazy(
                "Event from a customer that placed an order", "An order was placed"
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
        (
            NAME_ASSIGNED,
            pgettext_lazy(
                "Event from a staff user assigned a new name to a customer",
                "A customer's name was edited",
            ),
        ),
        (
            EMAIL_ASSIGNED,
            pgettext_lazy(
                "Event from a staff user assigned a new email address to a customer",
                "A customer's email address was edited",
            ),
        ),
        (
            NOTE_ADDED,
            pgettext_lazy(
                "Event from a staff user assigned a new email address to a customer",
                "A note was added to the customer",
            ),
        ),
    ]
