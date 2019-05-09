from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract import SingletonAPIResource


class Balance(SingletonAPIResource):
    OBJECT_NAME = "balance"
