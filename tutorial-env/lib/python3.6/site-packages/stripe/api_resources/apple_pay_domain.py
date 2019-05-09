from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract import CreateableAPIResource
from stripe.api_resources.abstract import DeletableAPIResource
from stripe.api_resources.abstract import ListableAPIResource


class ApplePayDomain(
    CreateableAPIResource, ListableAPIResource, DeletableAPIResource
):
    OBJECT_NAME = "apple_pay_domain"

    @classmethod
    def class_url(cls):
        return "/v1/apple_pay/domains"
