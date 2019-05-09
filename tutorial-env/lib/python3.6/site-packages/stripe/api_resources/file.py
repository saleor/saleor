from __future__ import absolute_import, division, print_function

import stripe
from stripe import api_requestor, util
from stripe.api_resources.abstract import ListableAPIResource


class File(ListableAPIResource):
    # This resource can have two different object names. In latter API
    # versions, only `file` is used, but since stripe-python may be used with
    # any API version, we need to support deserializing the older
    # `file_upload` object into the same class.
    OBJECT_NAME = "file"
    OBJECT_NAME_ALT = "file_upload"

    @classmethod
    def class_url(cls):
        return "/v1/files"

    @classmethod
    def create(
        cls, api_key=None, api_version=None, stripe_account=None, **params
    ):
        requestor = api_requestor.APIRequestor(
            api_key,
            api_base=stripe.upload_api_base,
            api_version=api_version,
            account=stripe_account,
        )
        url = cls.class_url()
        supplied_headers = {"Content-Type": "multipart/form-data"}
        response, api_key = requestor.request(
            "post", url, params=params, headers=supplied_headers
        )
        return util.convert_to_stripe_object(
            response, api_key, api_version, stripe_account
        )


# For backwards compatibility, the `File` class is aliased to `FileUpload`.
FileUpload = File
