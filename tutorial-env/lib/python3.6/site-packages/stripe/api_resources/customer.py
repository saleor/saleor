from __future__ import absolute_import, division, print_function

from stripe import api_requestor
from stripe.api_resources.abstract import CreateableAPIResource
from stripe.api_resources.abstract import DeletableAPIResource
from stripe.api_resources.abstract import UpdateableAPIResource
from stripe.api_resources.abstract import ListableAPIResource
from stripe.api_resources.abstract import custom_method
from stripe.api_resources.abstract import nested_resource_class_methods


@custom_method("delete_discount", http_verb="delete", http_path="discount")
@nested_resource_class_methods(
    "source", operations=["create", "retrieve", "update", "delete", "list"]
)
@nested_resource_class_methods(
    "tax_id", operations=["create", "retrieve", "delete", "list"]
)
class Customer(
    CreateableAPIResource,
    UpdateableAPIResource,
    ListableAPIResource,
    DeletableAPIResource,
):
    OBJECT_NAME = "customer"

    def delete_discount(self, **params):
        requestor = api_requestor.APIRequestor(
            self.api_key,
            api_version=self.stripe_version,
            account=self.stripe_account,
        )
        url = self.instance_url() + "/discount"
        _, api_key = requestor.request("delete", url, params)
        self.refresh_from({"discount": None}, api_key, True)
