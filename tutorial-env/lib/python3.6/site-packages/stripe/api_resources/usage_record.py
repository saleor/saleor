from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract.api_resource import APIResource
from stripe import api_requestor, util


class UsageRecord(APIResource):
    OBJECT_NAME = "usage_record"

    @classmethod
    def create(
        cls,
        api_key=None,
        idempotency_key=None,
        stripe_version=None,
        stripe_account=None,
        **params
    ):
        if "subscription_item" not in params:
            raise ValueError("Params must have a subscription_item key")

        subscription_item = params.pop("subscription_item")

        requestor = api_requestor.APIRequestor(
            api_key, api_version=stripe_version, account=stripe_account
        )
        url = "/v1/subscription_items/%s/usage_records" % subscription_item
        headers = util.populate_headers(idempotency_key)
        response, api_key = requestor.request("post", url, params, headers)

        return util.convert_to_stripe_object(
            response, api_key, stripe_version, stripe_account
        )
