from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract import CreateableAPIResource
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import ListableAPIResource
from stripe.api_resources.abstract import custom_method


@custom_method("details", http_verb="get")
class Card(CreateableAPIResource, ListableAPIResource, UpdateableAPIResource):
    OBJECT_NAME = "issuing.card"

    def details(self, idempotency_key=None, **params):
        return self.request("get", self.instance_url() + "/details", params)
