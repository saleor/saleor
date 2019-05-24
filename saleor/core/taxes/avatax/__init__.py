import json
from datetime import date
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from requests.auth import HTTPBasicAuth

from .. import charge_taxes_on_shipping

common_carrier_code = "FR020100"  # FIXME
cache_key = "avatax_checkout_id"


class TransactionType:
    INVOICE = "SalesInvoice"
    ORDER = "SalesOrder"


def get_api_url() -> str:
    """Based on settings return sanbox or production url"""
    if settings.AVATAX_USE_SANDBOX:
        return "https://sandbox-rest.avatax.com/api/v2/"
    return "https://rest.avatax.com/api/v2/"


def api_post_request(
    url: str,
    data: Dict[str, Any],
    username: str = settings.AVATAX_USERNAME_OR_ACCOUNT,
    password: str = settings.AVATAX_PASSWORD_OR_LICENSE,
) -> Dict[str, Any]:
    try:
        auth = HTTPBasicAuth(username, password)
        response = requests.post(url, auth=auth, data=json.dumps(data))
        print(auth)
        print(response.content)
    except requests.exceptions.RequestException:
        return {}
    return response.json()


def api_get_request(
    url,
    username=settings.AVATAX_USERNAME_OR_ACCOUNT,
    password=settings.AVATAX_PASSWORD_OR_LICENSE,
):
    return requests.get(url, auth=HTTPBasicAuth(username, password))


def validate_checkout(checkout: "Checkout") -> bool:
    """Validate if checkout object contains enough information to generate a request to
    avatax"""
    if not checkout.lines.count():
        return False

    shipping_address = checkout.shipping_address
    is_shipping_required = checkout.is_shipping_required
    address = shipping_address or checkout.billing_address
    if not is_shipping_required and not address:
        return False
    if not shipping_address:
        return False
    return True


def checkout_needs_new_fetch(data, checkout_token: str) -> bool:
    """We store the response from avatax for checkout object for given time. If object
    doesn't exist in cache or something has changed, then we fetch data from avatax."""
    checkout_cache_key = cache_key + checkout_token
    cached_checkout = cache.get(checkout_cache_key)

    if not cached_checkout:
        return True

    cached_request_data, cached_response = cached_checkout
    if data != cached_request_data:
        return True
    return False


def get_lines_data(checkout: "Checkout", discounts=None) -> List[Dict[str, str]]:
    data = []
    lines = checkout.lines.prefetch_related(
        "variant__product__category",
        "variant__product__collections",
        "variant__product__product_type",
    )
    for line in lines:
        description = line.variant.product.description

        data.append(
            {
                "quantity": line.quantity,
                "amount": str(line.get_total(discounts).net.amount),
                "taxCode": "PC040156",  # FIXME Should fetch taxcode from somewhere and save inside variant/product
                "itemCode": line.variant.sku,
                "description": description[:2000] if description else None,
            }
        )

    if charge_taxes_on_shipping() and checkout.shipping_method:
        data.append(
            {
                "quantity": 1,
                "amount": str(checkout.shipping_method.price.amount),
                "taxCode": common_carrier_code,
                "itemCode": "Shipping",
            }
        )
    return data


def generate_request_data(
    checkout: "Checkout",
    transaction_token=None,
    transaction_type=TransactionType.ORDER,
    commit=False,
    discounts=None,
):

    address = checkout.shipping_address or checkout.billing_address
    lines = get_lines_data(checkout, discounts)

    data = {
        "companyCode": settings.AVATAX_COMPANY_NAME,
        "type": transaction_type,
        "lines": lines,
        "code": transaction_token or str(checkout.token),
        "date": str(date.today()),
        "customerCode": checkout.user.id if checkout.user else None,
        # 'salespersonCode'
        # 'customerUsageType'
        # 'entityUseCode'
        # 'discount'
        # 'purchaseOrderNo'
        # 'exemptionNo'
        "addresses": {
            # FIXME we should put company address here
            "shipFrom": {  # warehouse
                "line1": "2000 Main Street",
                "city": "Irvine",
                "region": "CA",
                "country": "US",
                "postalCode": "92614",
            },
            "shipTo": {
                "line1": address.street_address_1,
                "line2": address.street_address_2,
                "city": address.city,
                "region": address.country_area,
                "country": address.country.code,
                "postalCode": address.postal_code,
            },
        },
        # parameters
        # referenceCode
        # reportingLocationCode
        # isSellerImporterOfRecord
        # businessIdentificationNo
        "commit": commit,
        # batchCode
        "currencyCode": settings.DEFAULT_CURRENCY,
        "email": checkout.email,
    }
    return data


def get_checkout_tax_data(checkout: "Checkout", discounts) -> Dict[str, Any]:
    checkout_cache_key = cache_key + str(checkout.token)
    data = generate_request_data(checkout, discounts=discounts)
    if checkout_needs_new_fetch(data, str(checkout.token)):
        transaction_url = urljoin(get_api_url(), "transactions/create")
        print("HIT TO API")
        response = api_post_request(transaction_url, data)
        if response and "error" not in response:
            cache.set(
                checkout_cache_key,
                (data, response),
                settings.AVATAX_CHECKOUT_CACHE_TIME,
            )
    else:
        _, response = cache.get(checkout_cache_key)

    return response
