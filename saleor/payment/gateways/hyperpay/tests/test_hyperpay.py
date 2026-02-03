"""Tests for HyperPay payment gateway."""

from decimal import Decimal
from unittest.mock import patch

import pytest

from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.gateways.hyperpay import (
    GATEWAY_NAME,
    GatewayConfig,
    authorize,
    capture,
    confirm,
    get_client_token,
    process_payment,
    refund,
    void,
)
from saleor.payment.gateways.hyperpay.consts import (
    DEFAULT_PAYMENT_BRANDS,
    DEFAULT_SUPPORTED_CURRENCIES,
)
from saleor.payment.interface import AddressData, PaymentData


@pytest.fixture
def gateway_config():
    """Create a test gateway configuration."""
    return GatewayConfig(
        gateway_name=GATEWAY_NAME,
        auto_capture=True,
        supported_currencies=DEFAULT_SUPPORTED_CURRENCIES,
        connection_params={
            "entity_id": "test_entity_id",
            "access_token": "test_access_token",
            "test_mode": True,
            "payment_brands": DEFAULT_PAYMENT_BRANDS,
        },
        store_customer=False,
    )


@pytest.fixture
def payment_data():
    """Create test payment data."""
    return PaymentData(
        gateway=GATEWAY_NAME,
        amount=Decimal("100.00"),
        currency="SAR",
        billing=AddressData(
            first_name="Test",
            last_name="User",
            company_name="",
            street_address_1="123 Test St",
            street_address_2="",
            city="Riyadh",
            city_area="",
            postal_code="12345",
            country="SA",
            country_area="",
            phone="",
            metadata=None,
            private_metadata=None,
        ),
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="1",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        token=None,
        _resolve_lines_data=lambda: None,
    )


class TestGetClientToken:
    """Tests for get_client_token function."""

    def test_returns_uuid_string(self):
        """Test that get_client_token returns a valid UUID string."""
        token = get_client_token()
        assert token is not None
        assert isinstance(token, str)
        assert len(token) == 36  # UUID format: 8-4-4-4-12


class TestAuthorize:
    """Tests for authorize function."""

    @patch("saleor.payment.gateways.hyperpay.hyperpay_api.prepare_checkout")
    def test_authorize_success(self, mock_prepare, gateway_config, payment_data):
        """Test successful authorization."""
        mock_prepare.return_value = {
            "checkout_id": "test_checkout_123",
            "result_code": "000.200.100",
            "result_description": "successfully created checkout",
        }

        response = authorize(payment_data, gateway_config)

        assert response.is_success is True
        assert response.action_required is True
        assert response.kind == TransactionKind.AUTH
        assert response.amount == payment_data.amount
        assert response.currency == payment_data.currency
        assert response.transaction_id == "test_checkout_123"
        assert response.error is None
        assert response.action_required_data is not None
        assert response.action_required_data["checkout_id"] == "test_checkout_123"

    @patch("saleor.payment.gateways.hyperpay.hyperpay_api.prepare_checkout")
    def test_authorize_failure(self, mock_prepare, gateway_config, payment_data):
        """Test failed authorization."""
        mock_prepare.return_value = {
            "error": "Invalid entity ID",
            "result_code": "100.100.100",
        }

        response = authorize(payment_data, gateway_config)

        assert response.is_success is False
        assert response.action_required is False
        assert response.kind == TransactionKind.AUTH
        assert response.error == "Invalid entity ID"


class TestCapture:
    """Tests for capture function."""

    @patch("saleor.payment.gateways.hyperpay.hyperpay_api.capture_payment")
    def test_capture_success(self, mock_capture, gateway_config, payment_data):
        """Test successful capture."""
        payment_data.token = "original_payment_123"
        mock_capture.return_value = {
            "success": True,
            "result_code": "000.000.000",
            "result_description": "Request successfully processed",
            "transaction_id": "capture_123",
        }

        response = capture(payment_data, gateway_config)

        assert response.is_success is True
        assert response.kind == TransactionKind.CAPTURE
        assert response.transaction_id == "capture_123"

    def test_capture_no_payment_id(self, gateway_config, payment_data):
        """Test capture without payment ID."""
        payment_data.token = None

        response = capture(payment_data, gateway_config)

        assert response.is_success is False
        assert response.error == "No payment ID provided for capture"


class TestRefund:
    """Tests for refund function."""

    @patch("saleor.payment.gateways.hyperpay.hyperpay_api.refund_payment")
    def test_refund_success(self, mock_refund, gateway_config, payment_data):
        """Test successful refund."""
        payment_data.token = "payment_to_refund_123"
        mock_refund.return_value = {
            "success": True,
            "result_code": "000.000.000",
            "result_description": "Request successfully processed",
            "transaction_id": "refund_123",
        }

        response = refund(payment_data, gateway_config)

        assert response.is_success is True
        assert response.kind == TransactionKind.REFUND
        assert response.transaction_id == "refund_123"

    def test_refund_no_payment_id(self, gateway_config, payment_data):
        """Test refund without payment ID."""
        payment_data.token = None

        response = refund(payment_data, gateway_config)

        assert response.is_success is False
        assert response.error == "No payment ID provided for refund"


class TestVoid:
    """Tests for void function."""

    @patch("saleor.payment.gateways.hyperpay.hyperpay_api.void_payment")
    def test_void_success(self, mock_void, gateway_config, payment_data):
        """Test successful void."""
        payment_data.token = "payment_to_void_123"
        mock_void.return_value = {
            "success": True,
            "result_code": "000.000.000",
            "result_description": "Request successfully processed",
            "transaction_id": "void_123",
        }

        response = void(payment_data, gateway_config)

        assert response.is_success is True
        assert response.kind == TransactionKind.VOID
        assert response.transaction_id == "void_123"

    def test_void_no_payment_id(self, gateway_config, payment_data):
        """Test void without payment ID."""
        payment_data.token = None

        response = void(payment_data, gateway_config)

        assert response.is_success is False
        assert response.error == "No payment ID provided for void"


class TestProcessPayment:
    """Tests for process_payment function."""

    @patch("saleor.payment.gateways.hyperpay.hyperpay_api.prepare_checkout")
    def test_process_payment_auto_capture(self, mock_prepare, gateway_config, payment_data):
        """Test process_payment with auto capture enabled."""
        mock_prepare.return_value = {
            "checkout_id": "checkout_auto_123",
            "result_code": "000.200.100",
            "result_description": "successfully created checkout",
        }

        response = process_payment(payment_data, gateway_config)

        assert response.is_success is True
        assert response.action_required is True
        assert response.kind == TransactionKind.CAPTURE  # Auto-capture mode
        assert response.action_required_data["payment_type"] == "DB"  # Debit

    @patch("saleor.payment.gateways.hyperpay.hyperpay_api.prepare_checkout")
    def test_process_payment_manual_capture(self, mock_prepare, payment_data):
        """Test process_payment with manual capture."""
        config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=False,  # Manual capture
            supported_currencies=DEFAULT_SUPPORTED_CURRENCIES,
            connection_params={
                "entity_id": "test_entity_id",
                "access_token": "test_access_token",
                "test_mode": True,
                "payment_brands": DEFAULT_PAYMENT_BRANDS,
            },
            store_customer=False,
        )

        mock_prepare.return_value = {
            "checkout_id": "checkout_manual_123",
            "result_code": "000.200.100",
            "result_description": "successfully created checkout",
        }

        response = process_payment(payment_data, config)

        assert response.is_success is True
        assert response.kind == TransactionKind.AUTH  # Pre-auth mode
        assert response.action_required_data["payment_type"] == "PA"  # Pre-auth
