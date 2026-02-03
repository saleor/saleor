"""HyperPay payment gateway core functions."""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ... import ChargeStatus, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData, PaymentMethodInfo
from . import hyperpay_api
from .consts import (
    DEFAULT_PAYMENT_BRANDS,
    DEFAULT_SUPPORTED_CURRENCIES,
    PAYMENT_TYPE_DEBIT,
    PAYMENT_TYPE_PREAUTH,
)


GATEWAY_NAME = "HyperPay"


@dataclass
class HyperPayConfig:
    """Configuration for HyperPay gateway."""

    entity_id: str
    access_token: str
    test_mode: bool = True
    payment_brands: str = DEFAULT_PAYMENT_BRANDS
    auto_capture: bool = True
    supported_currencies: str = DEFAULT_SUPPORTED_CURRENCIES


def get_hyperpay_config(config: GatewayConfig) -> HyperPayConfig:
    """Extract HyperPay-specific configuration from GatewayConfig."""
    params = config.connection_params
    return HyperPayConfig(
        entity_id=params.get("entity_id", ""),
        access_token=params.get("access_token", ""),
        test_mode=params.get("test_mode", True),
        payment_brands=params.get("payment_brands", DEFAULT_PAYMENT_BRANDS),
        auto_capture=config.auto_capture,
        supported_currencies=config.supported_currencies,
    )


def get_client_token(**_) -> str:
    """Return client token for HyperPay.

    For HyperPay, we return a UUID that will be used as the merchant transaction ID.
    """
    return str(uuid.uuid4())


def _create_billing_address(payment_info: PaymentData) -> dict[str, Any] | None:
    """Create billing address dict from payment info."""
    if not payment_info.billing:
        return None

    billing = payment_info.billing
    return {
        "street1": f"{billing.street_address_1} {billing.street_address_2}".strip(),
        "city": billing.city,
        "state": billing.country_area,
        "postcode": billing.postal_code,
        "country": billing.country,
    }


def _create_shipping_address(payment_info: PaymentData) -> dict[str, Any] | None:
    """Create shipping address dict from payment info."""
    if not payment_info.shipping:
        return None

    shipping = payment_info.shipping
    return {
        "street1": f"{shipping.street_address_1} {shipping.street_address_2}".strip(),
        "city": shipping.city,
        "state": shipping.country_area,
        "postcode": shipping.postal_code,
        "country": shipping.country,
    }


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Authorize payment with HyperPay.

    Creates a pre-authorization that can be captured later.
    """
    hp_config = get_hyperpay_config(config)

    # Use provided token or generate new one
    merchant_transaction_id = payment_information.token or get_client_token()

    result = hyperpay_api.prepare_checkout(
        entity_id=hp_config.entity_id,
        access_token=hp_config.access_token,
        amount=payment_information.amount,
        currency=payment_information.currency,
        payment_type=PAYMENT_TYPE_PREAUTH,
        payment_brands=hp_config.payment_brands,
        merchant_transaction_id=merchant_transaction_id,
        test_mode=hp_config.test_mode,
        customer_email=payment_information.customer_email,
        billing_address=_create_billing_address(payment_information),
        shipping_address=_create_shipping_address(payment_information),
    )

    if "error" in result:
        return GatewayResponse(
            is_success=False,
            action_required=False,
            kind=TransactionKind.AUTH,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=merchant_transaction_id,
            error=result.get("error"),
            payment_method_info=PaymentMethodInfo(
                type="hyperpay",
                brand="HyperPay",
                name="HyperPay",
            ),
        )

    checkout_id = result.get("checkout_id")

    return GatewayResponse(
        is_success=True,
        action_required=True,  # Customer needs to complete payment via HyperPay widget
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=checkout_id or merchant_transaction_id,
        error=None,
        action_required_data={
            "checkout_id": checkout_id,
            "merchant_transaction_id": merchant_transaction_id,
            "test_mode": hp_config.test_mode,
        },
        payment_method_info=PaymentMethodInfo(
            type="hyperpay",
            brand="HyperPay",
            name="HyperPay",
        ),
    )


def capture(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Capture a previously authorized payment."""
    hp_config = get_hyperpay_config(config)

    # The token should contain the payment ID from the original authorization
    payment_id = payment_information.token

    if not payment_id:
        return GatewayResponse(
            is_success=False,
            action_required=False,
            kind=TransactionKind.CAPTURE,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=str(uuid.uuid4()),
            error="No payment ID provided for capture",
        )

    result = hyperpay_api.capture_payment(
        payment_id=payment_id,
        entity_id=hp_config.entity_id,
        access_token=hp_config.access_token,
        amount=payment_information.amount,
        currency=payment_information.currency,
        test_mode=hp_config.test_mode,
    )

    return GatewayResponse(
        is_success=result.get("success", False),
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.get("transaction_id", payment_id),
        error=result.get("error") or result.get("result_description") if not result.get("success") else None,
        payment_method_info=PaymentMethodInfo(
            type="hyperpay",
            brand="HyperPay",
            name="HyperPay",
        ),
    )


def confirm(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Confirm payment after customer completes HyperPay widget flow."""
    hp_config = get_hyperpay_config(config)

    # The token should contain the checkout ID
    checkout_id = payment_information.token

    if not checkout_id:
        return GatewayResponse(
            is_success=False,
            action_required=False,
            kind=TransactionKind.CAPTURE,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=str(uuid.uuid4()),
            error="No checkout ID provided for confirmation",
        )

    result = hyperpay_api.get_payment_status(
        checkout_id=checkout_id,
        entity_id=hp_config.entity_id,
        access_token=hp_config.access_token,
        test_mode=hp_config.test_mode,
    )

    payment_id = result.get("payment_id", checkout_id)
    is_success = result.get("success", False)

    return GatewayResponse(
        is_success=is_success,
        action_required=False,
        kind=TransactionKind.CAPTURE if is_success else TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_id,
        error=result.get("error") or result.get("result_description") if not is_success else None,
        payment_method_info=PaymentMethodInfo(
            type="hyperpay",
            brand=result.get("payment_brand", "HyperPay"),
            name="HyperPay",
        ),
    )


def void(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Void/reverse a HyperPay payment."""
    hp_config = get_hyperpay_config(config)

    payment_id = payment_information.token

    if not payment_id:
        return GatewayResponse(
            is_success=False,
            action_required=False,
            kind=TransactionKind.VOID,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=str(uuid.uuid4()),
            error="No payment ID provided for void",
        )

    result = hyperpay_api.void_payment(
        payment_id=payment_id,
        entity_id=hp_config.entity_id,
        access_token=hp_config.access_token,
        test_mode=hp_config.test_mode,
    )

    return GatewayResponse(
        is_success=result.get("success", False),
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.get("transaction_id", payment_id),
        error=result.get("error") or result.get("result_description") if not result.get("success") else None,
        payment_method_info=PaymentMethodInfo(
            type="hyperpay",
            brand="HyperPay",
            name="HyperPay",
        ),
    )


def refund(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Refund a HyperPay payment."""
    hp_config = get_hyperpay_config(config)

    payment_id = payment_information.token

    if not payment_id:
        return GatewayResponse(
            is_success=False,
            action_required=False,
            kind=TransactionKind.REFUND,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=str(uuid.uuid4()),
            error="No payment ID provided for refund",
        )

    result = hyperpay_api.refund_payment(
        payment_id=payment_id,
        entity_id=hp_config.entity_id,
        access_token=hp_config.access_token,
        amount=payment_information.amount,
        currency=payment_information.currency,
        test_mode=hp_config.test_mode,
    )

    return GatewayResponse(
        is_success=result.get("success", False),
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.get("transaction_id", payment_id),
        error=result.get("error") or result.get("result_description") if not result.get("success") else None,
        payment_method_info=PaymentMethodInfo(
            type="hyperpay",
            brand="HyperPay",
            name="HyperPay",
        ),
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process HyperPay payment.

    Depending on auto_capture setting:
    - If True: Create a debit (immediate capture) transaction
    - If False: Create a pre-authorization (capture later)
    """
    hp_config = get_hyperpay_config(config)

    merchant_transaction_id = payment_information.token or get_client_token()
    payment_type = PAYMENT_TYPE_DEBIT if hp_config.auto_capture else PAYMENT_TYPE_PREAUTH

    result = hyperpay_api.prepare_checkout(
        entity_id=hp_config.entity_id,
        access_token=hp_config.access_token,
        amount=payment_information.amount,
        currency=payment_information.currency,
        payment_type=payment_type,
        payment_brands=hp_config.payment_brands,
        merchant_transaction_id=merchant_transaction_id,
        test_mode=hp_config.test_mode,
        customer_email=payment_information.customer_email,
        billing_address=_create_billing_address(payment_information),
        shipping_address=_create_shipping_address(payment_information),
    )

    if "error" in result:
        return GatewayResponse(
            is_success=False,
            action_required=False,
            kind=TransactionKind.CAPTURE if hp_config.auto_capture else TransactionKind.AUTH,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=merchant_transaction_id,
            error=result.get("error"),
            payment_method_info=PaymentMethodInfo(
                type="hyperpay",
                brand="HyperPay",
                name="HyperPay",
            ),
        )

    checkout_id = result.get("checkout_id")

    return GatewayResponse(
        is_success=True,
        action_required=True,  # Customer needs to complete payment via HyperPay widget
        kind=TransactionKind.CAPTURE if hp_config.auto_capture else TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=checkout_id or merchant_transaction_id,
        error=None,
        action_required_data={
            "checkout_id": checkout_id,
            "merchant_transaction_id": merchant_transaction_id,
            "test_mode": hp_config.test_mode,
            "payment_type": payment_type,
        },
        payment_method_info=PaymentMethodInfo(
            type="hyperpay",
            brand="HyperPay",
            name="HyperPay",
        ),
    )
