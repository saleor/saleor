from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.api_resources.abstract import ListableAPIResource
from stripe.api_resources.abstract import nested_resource_class_methods


@nested_resource_class_methods(
    "refund", operations=["create", "retrieve", "update", "list"]
)
class ApplicationFee(ListableAPIResource):
    OBJECT_NAME = "application_fee"

    def refund(self, idempotency_key=None, **params):
        headers = util.populate_headers(idempotency_key)
        url = self.instance_url() + "/refund"
        self.refresh_from(self.request("post", url, params, headers))
        return self
