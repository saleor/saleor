from decimal import Decimal

import pytest

from .... import ChargeStatus, PaymentError, TransactionKind, gateway
from ....models import Payment


@pytest.fixture
def payment_shop2shop(db, order_with_lines):
    return Payment.objects.create(
        gateway="yebofresh.payments.shop2shop",
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
def shop2shop_payment_txn_preauth(order_with_lines, payment_shop2shop):
    order = order_with_lines
    payment = payment_shop2shop
    payment.order = order
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.AUTH,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def shop2shop_payment_txn_captured(order_with_lines, payment_shop2shop):
    order = order_with_lines
    payment = payment_shop2shop
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def shop2shop_payment_txn_to_confirm(order_with_lines, payment_shop2shop):
    order = order_with_lines
    payment = payment_shop2shop
    payment.order = order
    payment.to_confirm = True
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        gateway_response={},
        is_success=True,
        action_required=True,
    )
    return payment


@pytest.fixture
def shop2shop_payment_txn_refunded(order_with_lines, payment_shop2shop):
    order = order_with_lines
    payment = payment_shop2shop
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.is_active = False
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.REFUND,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def shop2shop_payment_not_authorized(payment_shop2shop):
    payment_shop2shop.is_active = False
    payment_shop2shop.save()
    return payment_shop2shop


@pytest.fixture(autouse=True)
def setup_shop2shop_gateway(settings):
    settings.PLUGINS = [
        "saleor.payment.gateways.shop2shop.plugin.Shop2ShopGatewayPlugin"]
    return settings


def test_shop2shop_authorize_success(payment_shop2shop):
    txn = gateway.authorize(payment=payment_shop2shop, token="Fake")
    assert txn.is_success
    assert txn.kind == TransactionKind.AUTH
    assert txn.payment == payment_shop2shop
    payment_shop2shop.refresh_from_db()
    assert payment_shop2shop.is_active


@pytest.mark.parametrize(
    "is_active, charge_status",
    [
        (False, ChargeStatus.NOT_CHARGED),
        (False, ChargeStatus.PARTIALLY_CHARGED),
        (False, ChargeStatus.FULLY_CHARGED),
        (False, ChargeStatus.PARTIALLY_REFUNDED),
        (False, ChargeStatus.FULLY_REFUNDED),
        (True, ChargeStatus.PARTIALLY_CHARGED),
        (True, ChargeStatus.FULLY_CHARGED),
        (True, ChargeStatus.PARTIALLY_REFUNDED),
        (True, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_shop2shop_authorize_failed(is_active, charge_status, payment_shop2shop):
    payment = payment_shop2shop
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.authorize(payment=payment, token="Fake")
        assert txn is None


def test_shop2shop_authorize_gateway_error(payment_shop2shop, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.shop2shop.shop2shop_success",
                        lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway.authorize(payment=payment_shop2shop, token="Fake")
        assert txn.kind == TransactionKind.AUTH
        assert not txn.is_success
        assert txn.payment == payment_shop2shop


def test_shop2shop_void_success(shop2shop_payment_txn_preauth):
    assert shop2shop_payment_txn_preauth.is_active
    assert shop2shop_payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    txn = gateway.void(payment=shop2shop_payment_txn_preauth)
    assert txn.is_success
    assert txn.kind == TransactionKind.VOID
    assert txn.payment == shop2shop_payment_txn_preauth
    shop2shop_payment_txn_preauth.refresh_from_db()
    assert not shop2shop_payment_txn_preauth.is_active
    assert shop2shop_payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED


@pytest.mark.parametrize(
    "is_active, charge_status",
    [
        (False, ChargeStatus.NOT_CHARGED),
        (False, ChargeStatus.PARTIALLY_CHARGED),
        (False, ChargeStatus.FULLY_CHARGED),
        (False, ChargeStatus.PARTIALLY_REFUNDED),
        (False, ChargeStatus.FULLY_REFUNDED),
        (True, ChargeStatus.PARTIALLY_CHARGED),
        (True, ChargeStatus.FULLY_CHARGED),
        (True, ChargeStatus.PARTIALLY_REFUNDED),
        (True, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_shop2shop_void_failed(is_active, charge_status, payment_shop2shop):
    payment = payment_shop2shop
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.void(payment=payment)
        assert txn is None


def test_shop2shop_void_gateway_error(shop2shop_payment_txn_preauth, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.shop2shop.shop2shop_success",
                        lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway.void(payment=shop2shop_payment_txn_preauth)
        assert txn.kind == TransactionKind.VOID
        assert not txn.is_success
        assert txn.payment == shop2shop_payment_txn_preauth


@pytest.mark.parametrize(
    "amount, charge_status",
    [("98.40", ChargeStatus.FULLY_CHARGED), (70, ChargeStatus.PARTIALLY_CHARGED)],
)
def test_shop2shop_capture_success(amount, charge_status, shop2shop_payment_txn_preauth):
    txn = gateway.capture(payment=shop2shop_payment_txn_preauth, amount=Decimal(amount))
    assert txn.is_success
    assert txn.payment == shop2shop_payment_txn_preauth
    shop2shop_payment_txn_preauth.refresh_from_db()
    assert shop2shop_payment_txn_preauth.charge_status == charge_status
    assert shop2shop_payment_txn_preauth.is_active


@pytest.mark.parametrize(
    "amount, captured_amount, charge_status, is_active",
    [
        (80, 0, ChargeStatus.NOT_CHARGED, False),
        (120, 0, ChargeStatus.NOT_CHARGED, True),
        (80, 20, ChargeStatus.PARTIALLY_CHARGED, True),
        (80, 80, ChargeStatus.FULLY_CHARGED, True),
        (80, 0, ChargeStatus.FULLY_REFUNDED, True),
    ],
)
def test_shop2shop_capture_failed(
    amount, captured_amount, charge_status, is_active, payment_shop2shop
):
    payment = payment_shop2shop
    payment.is_active = is_active
    payment.captured_amount = captured_amount
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.capture(payment=payment, amount=amount)
        assert txn is None


def test_shop2shop_capture_gateway_error(shop2shop_payment_txn_preauth, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.shop2shop.shop2shop_success",
                        lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway.capture(payment=shop2shop_payment_txn_preauth, amount=80)
        assert txn.kind == TransactionKind.CAPTURE
        assert not txn.is_success
        assert txn.payment == shop2shop_payment_txn_preauth


@pytest.mark.parametrize(
    (
        "initial_captured_amount, refund_amount, final_captured_amount, "
        "final_charge_status, active_after"
    ),
    [
        (80, 80, 0, ChargeStatus.FULLY_REFUNDED, False),
        (80, 10, 70, ChargeStatus.PARTIALLY_REFUNDED, True),
    ],
)
def test_shop2shop_refund_success(
    initial_captured_amount,
    refund_amount,
    final_captured_amount,
    final_charge_status,
    active_after,
    shop2shop_payment_txn_captured,
):
    payment = shop2shop_payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = initial_captured_amount
    payment.save()
    txn = gateway.refund(payment=payment, amount=Decimal(refund_amount))

    payment.refresh_from_db()
    assert txn.kind == TransactionKind.REFUND
    assert txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == final_charge_status
    assert payment.captured_amount == final_captured_amount
    assert payment.is_active == active_after


@pytest.mark.parametrize(
    "initial_captured_amount, refund_amount, initial_charge_status",
    [
        (0, 10, ChargeStatus.NOT_CHARGED),
        (10, 20, ChargeStatus.PARTIALLY_CHARGED),
        (10, 20, ChargeStatus.FULLY_CHARGED),
        (10, 20, ChargeStatus.PARTIALLY_REFUNDED),
        (80, 0, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_shop2shop_refund_failed(
    initial_captured_amount, refund_amount, initial_charge_status, payment_shop2shop
):
    payment = payment_shop2shop
    payment.charge_status = initial_charge_status
    payment.captured_amount = Decimal(initial_captured_amount)
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.refund(payment=payment, amount=Decimal(refund_amount))
        assert txn is None


def test_shop2shop_refund_gateway_error(shop2shop_payment_txn_captured, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.shop2shop.shop2shop_success",
                        lambda: False)
    payment = shop2shop_payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = Decimal("80.00")
    payment.save()
    with pytest.raises(PaymentError):
        gateway.refund(payment=payment, amount=Decimal("80.00"))

    payment.refresh_from_db()
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == Decimal("80.00")
