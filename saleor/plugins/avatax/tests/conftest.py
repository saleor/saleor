import pytest

from ....account.models import Address
from ....checkout.fetch import CheckoutInfo
from ....shipping.models import ShippingMethodChannelListing
from ...models import PluginConfiguration
from ..plugin import AvataxPlugin


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("Authorization", "Basic Og==")],
    }


@pytest.fixture
def plugin_configuration(db):
    def set_configuration(
        username="test",
        password="test",
        sandbox=False,
    ):
        data = {
            "active": True,
            "name": AvataxPlugin.PLUGIN_NAME,
            "configuration": [
                {"name": "Username or account", "value": username},
                {"name": "Password or license", "value": password},
                {"name": "Use sandbox", "value": sandbox},
                {"name": "Company name", "value": "DEFAULT"},
                {"name": "Autocommit", "value": False},
            ],
        }
        configuration = PluginConfiguration.objects.create(
            identifier=AvataxPlugin.PLUGIN_ID, **data
        )
        return configuration

    return set_configuration


@pytest.fixture
def ship_to_pl_address(db):
    return Address.objects.create(
        first_name="Eleanor",
        last_name="Smith",
        street_address_1="Oławska 10",
        city="WROCŁAW",
        postal_code="53-105",
        country="PL",
        phone="+48713988155",
    )


@pytest.fixture
def checkout_with_items_and_shipping(checkout_with_items, address, shipping_method):
    checkout_with_items.shipping_address = address
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.billing_address = address
    checkout_with_items.save()
    return checkout_with_items


@pytest.fixture
def checkout_with_items_and_shipping_info(checkout_with_items_and_shipping):
    checkout = checkout_with_items_and_shipping
    channel = checkout.channel
    shipping_address = checkout.shipping_address
    shipping_method = checkout.shipping_method
    shipping_channel_listings = ShippingMethodChannelListing.objects.filter(
        shipping_method=shipping_method, channel=channel
    ).first()
    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        shipping_method_channel_listings=shipping_channel_listings,
        valid_shipping_methods=[],
    )
    return checkout_info


@pytest.fixture
def avalara_response_for_checkout_with_items_and_shipping():
    return {
        "id": 0,
        "code": "8657e84b-c5ab-4c27-bcc2-c8d3ebbe771b",
        "companyId": 242975,
        "date": "2021-03-18",
        "paymentDate": "2021-03-18",
        "status": "Temporary",
        "type": "SalesOrder",
        "batchCode": "",
        "currencyCode": "USD",
        "exchangeRateCurrencyCode": "USD",
        "customerUsageType": "",
        "entityUseCode": "",
        "customerVendorCode": "0",
        "customerCode": "0",
        "exemptNo": "",
        "reconciled": False,
        "locationCode": "",
        "reportingLocationCode": "",
        "purchaseOrderNo": "",
        "referenceCode": "",
        "salespersonCode": "",
        "totalAmount": 12.2,
        "totalExempt": 0.0,
        "totalDiscount": 0.0,
        "totalTax": 2.8,
        "totalTaxable": 12.2,
        "totalTaxCalculated": 2.8,
        "adjustmentReason": "NotAdjusted",
        "locked": False,
        "version": 1,
        "exchangeRateEffectiveDate": "2021-03-18",
        "exchangeRate": 1.0,
        "email": "",
        "modifiedDate": "2021-03-18T13:23:21.7641305Z",
        "modifiedUserId": 283192,
        "taxDate": "2021-03-18T00:00:00Z",
        "lines": [
            {
                "id": 0,
                "transactionId": 0,
                "lineNumber": "1",
                "customerUsageType": "",
                "entityUseCode": "",
                "description": "Test product",
                "discountAmount": 0.0,
                "exemptAmount": 0.0,
                "exemptCertId": 0,
                "exemptNo": "",
                "isItemTaxable": True,
                "itemCode": "123",
                "lineAmount": 4.07,
                "quantity": 1.0,
                "ref1": "",
                "ref2": "",
                "reportingDate": "2021-03-18",
                "tax": 0.93,
                "taxableAmount": 4.07,
                "taxCalculated": 0.93,
                "taxCode": "O9999999",
                "taxCodeId": 5340,
                "taxDate": "2021-03-18",
                "taxIncluded": True,
                "details": [
                    {
                        "id": 0,
                        "transactionLineId": 0,
                        "transactionId": 0,
                        "country": "PL",
                        "region": "PL",
                        "exemptAmount": 0.0,
                        "jurisCode": "PL",
                        "jurisName": "POLAND",
                        "stateAssignedNo": "",
                        "jurisType": "CNT",
                        "jurisdictionType": "Country",
                        "nonTaxableAmount": 0.0,
                        "rate": 0.23,
                        "tax": 0.93,
                        "taxableAmount": 4.07,
                        "taxType": "Output",
                        "taxSubTypeId": "O",
                        "taxName": "Standard Rate",
                        "taxAuthorityTypeId": 45,
                        "taxCalculated": 0.93,
                        "rateType": "Standard",
                        "rateTypeCode": "S",
                        "unitOfBasis": "PerCurrencyUnit",
                        "isNonPassThru": False,
                        "isFee": False,
                        "reportingTaxableUnits": 4.07,
                        "reportingNonTaxableUnits": 0.0,
                        "reportingExemptUnits": 0.0,
                        "reportingTax": 0.93,
                        "reportingTaxCalculated": 0.93,
                        "liabilityType": "Seller",
                    }
                ],
                "nonPassthroughDetails": [],
                "hsCode": "",
                "costInsuranceFreight": 0.0,
                "vatCode": "PLS-230O--PL",
                "vatNumberTypeId": 0,
            },
            {
                "id": 0,
                "transactionId": 0,
                "lineNumber": "2",
                "customerUsageType": "",
                "entityUseCode": "",
                "discountAmount": 0.0,
                "exemptAmount": 0.0,
                "exemptCertId": 0,
                "exemptNo": "",
                "isItemTaxable": True,
                "itemCode": "Shipping",
                "lineAmount": 8.13,
                "quantity": 1.0,
                "ref1": "",
                "ref2": "",
                "reportingDate": "2021-03-18",
                "tax": 1.87,
                "taxableAmount": 8.13,
                "taxCalculated": 1.87,
                "taxCode": "FR020100",
                "taxCodeId": 4784,
                "taxDate": "2021-03-18",
                "taxIncluded": True,
                "details": [
                    {
                        "id": 0,
                        "transactionLineId": 0,
                        "transactionId": 0,
                        "country": "PL",
                        "region": "PL",
                        "exemptAmount": 0.0,
                        "jurisCode": "PL",
                        "jurisName": "POLAND",
                        "stateAssignedNo": "",
                        "jurisType": "CNT",
                        "jurisdictionType": "Country",
                        "nonTaxableAmount": 0.0,
                        "rate": 0.23,
                        "tax": 1.87,
                        "taxableAmount": 8.13,
                        "taxType": "Output",
                        "taxSubTypeId": "O",
                        "taxName": "Standard Rate",
                        "taxAuthorityTypeId": 45,
                        "taxCalculated": 1.87,
                        "rateType": "Standard",
                        "rateTypeCode": "S",
                        "unitOfBasis": "PerCurrencyUnit",
                        "isNonPassThru": False,
                        "isFee": False,
                        "reportingTaxableUnits": 8.13,
                        "reportingNonTaxableUnits": 0.0,
                        "reportingExemptUnits": 0.0,
                        "reportingTax": 1.87,
                        "reportingTaxCalculated": 1.87,
                        "liabilityType": "Seller",
                    }
                ],
                "nonPassthroughDetails": [],
                "hsCode": "",
                "costInsuranceFreight": 0.0,
                "vatCode": "PLS-230F--PL",
                "vatNumberTypeId": 0,
            },
        ],
        "addresses": [
            {
                "id": 0,
                "transactionId": 0,
                "boundaryLevel": "Zip5",
                "line1": "Teczowa 7",
                "line2": "",
                "line3": "",
                "city": "WROCLAW",
                "region": "",
                "postalCode": "53-601",
                "country": "PL",
                "taxRegionId": 205102,
                "latitude": "",
                "longitude": "",
            }
        ],
        "summary": [
            {
                "country": "PL",
                "region": "PL",
                "jurisType": "Country",
                "jurisCode": "PL",
                "jurisName": "POLAND",
                "taxAuthorityType": 45,
                "stateAssignedNo": "",
                "taxType": "Output",
                "taxSubType": "O",
                "taxName": "Standard Rate",
                "rateType": "Standard",
                "taxable": 12.2,
                "rate": 0.23,
                "tax": 2.8,
                "taxCalculated": 2.8,
                "nonTaxable": 0.0,
                "exemption": 0.0,
            }
        ],
    }
