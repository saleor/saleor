from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.api_resources.abstract import CreateableAPIResource
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import ListableAPIResource
from stripe.api_resources.abstract import nested_resource_class_methods
from stripe.api_resources.abstract import custom_method


@custom_method("cancel", http_verb="post")
@custom_method("release", http_verb="post")
@nested_resource_class_methods("revision", operations=["retrieve", "list"])
class SubscriptionSchedule(
    CreateableAPIResource, UpdateableAPIResource, ListableAPIResource
):
    OBJECT_NAME = "subscription_schedule"

    def cancel(self, idempotency_key=None, **params):
        url = self.instance_url() + "/cancel"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self

    def release(self, idempotency_key=None, **params):
        url = self.instance_url() + "/release"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self

    def revisions(self, **params):
        return self.request("get", self.instance_url() + "/revisions", params)
