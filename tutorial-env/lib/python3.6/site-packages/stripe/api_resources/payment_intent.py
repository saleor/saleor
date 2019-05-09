from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.api_resources.abstract import CreateableAPIResource
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import ListableAPIResource
from stripe.api_resources.abstract import custom_method


@custom_method("cancel", http_verb="post")
@custom_method("capture", http_verb="post")
@custom_method("confirm", http_verb="post")
class PaymentIntent(
    CreateableAPIResource, UpdateableAPIResource, ListableAPIResource
):
    OBJECT_NAME = "payment_intent"

    def cancel(self, idempotency_key=None, **params):
        url = self.instance_url() + "/cancel"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self

    def capture(self, idempotency_key=None, **params):
        url = self.instance_url() + "/capture"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self

    def confirm(self, idempotency_key=None, **params):
        url = self.instance_url() + "/confirm"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self
