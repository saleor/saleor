from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import ListableAPIResource
from stripe.api_resources.abstract import custom_method


@custom_method("approve", http_verb="post")
@custom_method("decline", http_verb="post")
class Authorization(ListableAPIResource, UpdateableAPIResource):
    OBJECT_NAME = "issuing.authorization"

    def approve(self, idempotency_key=None, **params):
        url = self.instance_url() + "/approve"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self

    def decline(self, idempotency_key=None, **params):
        url = self.instance_url() + "/decline"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self
