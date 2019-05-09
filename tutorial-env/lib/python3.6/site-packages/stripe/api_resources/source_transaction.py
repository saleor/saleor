from __future__ import absolute_import, division, print_function

from stripe.stripe_object import StripeObject


class SourceTransaction(StripeObject):
    OBJECT_NAME = "source_transaction"
