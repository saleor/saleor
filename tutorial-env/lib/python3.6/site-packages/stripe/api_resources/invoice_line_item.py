from __future__ import absolute_import, division, print_function

from stripe.stripe_object import StripeObject


class InvoiceLineItem(StripeObject):
    OBJECT_NAME = "line_item"
