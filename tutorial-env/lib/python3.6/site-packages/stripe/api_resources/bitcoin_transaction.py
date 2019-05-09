from __future__ import absolute_import, division, print_function

from stripe.stripe_object import StripeObject


class BitcoinTransaction(StripeObject):
    OBJECT_NAME = "bitcoin_transaction"
