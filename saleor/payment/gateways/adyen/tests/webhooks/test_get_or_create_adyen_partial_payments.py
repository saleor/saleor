from decimal import Decimal

from ...webhooks import get_or_create_adyen_partial_payments


def test_get_or_create_adyen_partial_payments_with_additional_actions_response(
    payment_adyen_for_checkout,
):
    # given
    notification_data = {
        "additionalData": {
            "order-2-paymentMethod": "visa",
            "threeds2.cardEnrolled": "false",
            "order-2-pspReference": "861643021198177D",
            "order-2-paymentAmount": "GBP 16.29",
            "recurringProcessingModel": "Subscription",
            "paymentMethod": "visa",
            "order-1-pspReference": "861643021155073F",
            "order-1-paymentAmount": "GBP 14.71",
            "order-1-paymentMethod": "givex",
        },
        "pspReference": "861643021198177D",
        "resultCode": "Authorised",
        "merchantReference": "UGF5bWVudDoyNw==",
        "paymentMethod": "visa",
        "shopperLocale": "en_GB",
    }

    checkout = payment_adyen_for_checkout.checkout

    # when
    get_or_create_adyen_partial_payments(notification_data, payment_adyen_for_checkout)

    # then
    partial_payments = list(checkout.payments.exclude(id=payment_adyen_for_checkout.id))

    assert len(partial_payments) == 2
    assert all([payment.is_active is False for payment in partial_payments])
    assert all([payment.partial is True for payment in partial_payments])
    assert all([payment.is_active is False for payment in partial_payments])
    assert any(payment.total == Decimal("14.71") for payment in partial_payments)
    assert any(payment.total == Decimal("16.29") for payment in partial_payments)
    assert any(
        payment.psp_reference == "861643021155073F" for payment in partial_payments
    )
    assert any(
        payment.psp_reference == "861643021198177D" for payment in partial_payments
    )


def test_get_or_create_adyen_partial_payments_with_notification_payload(
    notification, payment_adyen_for_checkout
):
    # given
    notification_data = notification()
    notification_data["additionalData"] = {
        "order-2-paymentMethod": "visa",
        "order-2-pspReference": "881643125782168B",
        "order-2-paymentAmount": "GBP 29.10",
        "order-1-pspReference": "861643125754056E",
        "order-1-paymentAmount": "GBP 41.90",
        "order-1-paymentMethod": "givex",
    }

    checkout = payment_adyen_for_checkout.checkout

    # when
    get_or_create_adyen_partial_payments(notification_data, payment_adyen_for_checkout)

    # then
    partial_payments = list(checkout.payments.exclude(id=payment_adyen_for_checkout.id))

    assert len(partial_payments) == 2
    assert all([payment.is_active is False for payment in partial_payments])
    assert all([payment.partial is True for payment in partial_payments])
    assert all([payment.is_active is False for payment in partial_payments])
    assert any(payment.total == Decimal("29.10") for payment in partial_payments)
    assert any(payment.total == Decimal("41.90") for payment in partial_payments)
    assert any(
        payment.psp_reference == "881643125782168B" for payment in partial_payments
    )
    assert any(
        payment.psp_reference == "861643125754056E" for payment in partial_payments
    )
