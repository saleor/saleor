import pytest

from ....payment import ChargeStatus, TransactionKind
from ....payment.models import Payment
from ....webhook.transport.utils import to_payment_app_id


@pytest.fixture
def payment_dummy(db, order_with_lines):
    return Payment.objects.create(
        gateway="mirumee.payments.dummy",
        order=order_with_lines,
        is_active=True,
        cc_first_digits="4111",
        cc_last_digits="1111",
        cc_brand="visa",
        cc_exp_month=12,
        cc_exp_year=2027,
        total=order_with_lines.total.gross.amount,
        currency=order_with_lines.currency,
        billing_first_name=order_with_lines.billing_address.first_name,
        billing_last_name=order_with_lines.billing_address.last_name,
        billing_company_name=order_with_lines.billing_address.company_name,
        billing_address_1=order_with_lines.billing_address.street_address_1,
        billing_address_2=order_with_lines.billing_address.street_address_2,
        billing_city=order_with_lines.billing_address.city,
        billing_postal_code=order_with_lines.billing_address.postal_code,
        billing_country_code=order_with_lines.billing_address.country.code,
        billing_country_area=order_with_lines.billing_address.country_area,
        billing_email=order_with_lines.user_email,
    )


@pytest.fixture
def payment_not_authorized(payment_dummy):
    payment_dummy.is_active = False
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payments_dummy(order_with_lines):
    return Payment.objects.bulk_create(
        [
            Payment(
                gateway="mirumee.payments.dummy",
                order=order_with_lines,
                is_active=True,
                cc_first_digits="4111",
                cc_last_digits="1111",
                cc_brand="visa",
                cc_exp_month=12,
                cc_exp_year=2027,
                total=order_with_lines.total.gross.amount,
                currency=order_with_lines.currency,
                billing_first_name=order_with_lines.billing_address.first_name,
                billing_last_name=order_with_lines.billing_address.last_name,
                billing_company_name=order_with_lines.billing_address.company_name,
                billing_address_1=order_with_lines.billing_address.street_address_1,
                billing_address_2=order_with_lines.billing_address.street_address_2,
                billing_city=order_with_lines.billing_address.city,
                billing_postal_code=order_with_lines.billing_address.postal_code,
                billing_country_code=order_with_lines.billing_address.country.code,
                billing_country_area=order_with_lines.billing_address.country_area,
                billing_email=order_with_lines.user_email,
            )
            for _ in range(3)
        ]
    )


@pytest.fixture
def payment(payment_dummy, payment_app):
    gateway_id = "credit-card"
    gateway = to_payment_app_id(payment_app, gateway_id)
    payment_dummy.gateway = gateway
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payment_cancelled(payment_dummy):
    payment_dummy.charge_status = ChargeStatus.CANCELLED
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payment_dummy_fully_charged(payment_dummy):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payment_dummy_credit_card(db, order_with_lines):
    return Payment.objects.create(
        gateway="mirumee.payments.dummy_credit_card",
        order=order_with_lines,
        is_active=True,
        cc_first_digits="4111",
        cc_last_digits="1111",
        cc_brand="visa",
        cc_exp_month=12,
        cc_exp_year=2027,
        total=order_with_lines.total.gross.amount,
        currency=order_with_lines.total.gross.currency,
        billing_first_name=order_with_lines.billing_address.first_name,
        billing_last_name=order_with_lines.billing_address.last_name,
        billing_company_name=order_with_lines.billing_address.company_name,
        billing_address_1=order_with_lines.billing_address.street_address_1,
        billing_address_2=order_with_lines.billing_address.street_address_2,
        billing_city=order_with_lines.billing_address.city,
        billing_postal_code=order_with_lines.billing_address.postal_code,
        billing_country_code=order_with_lines.billing_address.country.code,
        billing_country_area=order_with_lines.billing_address.country_area,
        billing_email=order_with_lines.user_email,
    )


@pytest.fixture
def payment_txn_preauth(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        currency=payment.currency,
        kind=TransactionKind.AUTH,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_txn_captured(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        currency=payment.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_txn_capture_failed(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.REFUSED
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        currency=payment.currency,
        kind=TransactionKind.CAPTURE_FAILED,
        gateway_response={
            "status": 403,
            "errorCode": "901",
            "message": "Invalid Merchant Account",
            "errorType": "security",
        },
        error="invalid",
        is_success=False,
    )
    return payment


@pytest.fixture
def payment_txn_to_confirm(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.to_confirm = True
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        currency=payment.currency,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        gateway_response={},
        is_success=True,
        action_required=True,
    )
    return payment


@pytest.fixture
def payment_txn_refunded(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.is_active = False
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        currency=payment.currency,
        kind=TransactionKind.REFUND,
        gateway_response={},
        is_success=True,
    )
    return payment
