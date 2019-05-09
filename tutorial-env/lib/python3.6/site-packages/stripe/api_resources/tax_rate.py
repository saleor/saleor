from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract import CreateableAPIResource
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import ListableAPIResource


class TaxRate(
    CreateableAPIResource, UpdateableAPIResource, ListableAPIResource
):
    OBJECT_NAME = "tax_rate"
