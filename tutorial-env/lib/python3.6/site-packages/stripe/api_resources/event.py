from __future__ import absolute_import, division, print_function

from stripe.api_resources import abstract


class Event(abstract.ListableAPIResource):
    OBJECT_NAME = "event"
