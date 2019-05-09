from __future__ import absolute_import, division, print_function

from stripe.stripe_object import StripeObject


class CardDetails(StripeObject):
    OBJECT_NAME = "issuing.card_details"
