from __future__ import absolute_import, division, print_function

from stripe.stripe_object import StripeObject


class LoginLink(StripeObject):
    OBJECT_NAME = "login_link"
