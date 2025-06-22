import json
import hashlib
import hmac
from unittest.mock import patch
from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
import pytest
from django.core.cache import cache
from urllib.parse import urlencode

from ......account.error_codes import AccountErrorCode
from .....tests.utils import get_graphql_content
from saleor.account.models import User
from saleor.graphql.account.mutations.authentication.telegram_email_change_request import (
    TelegramEmailChangeRequest,
    _verification_codes,
    _verification_lock,
    cleanup_expired_codes,
)
from saleor.graphql.account.mutations.authentication.telegram_email_change_confirm import (
    TelegramEmailChangeConfirm,
)

TELEGRAM_EMAIL_CHANGE_REQUEST_MUTATION = """
    mutation telegramEmailChangeRequest($initDataRaw: String!, $oldEmail: String!, $newEmail: String!) {
        telegramEmailChangeRequest(initDataRaw: $initDataRaw, oldEmail: $oldEmail, newEmail: $newEmail) {
            user {
                email
                firstName
                lastName
            }
            verificationCode
            expiresAt
            errors {
                field
                message
                code
            }
        }
    }
"""

TELEGRAM_EMAIL_CHANGE_CONFIRM_MUTATION = """
    mutation telegramEmailChangeConfirm($initDataRaw: String!, $verificationCode: String!, $oldEmail: String!, $newEmail: String!) {
        telegramEmailChangeConfirm(initDataRaw: $initDataRaw, verificationCode: $verificationCode, oldEmail: $oldEmail, newEmail: $newEmail) {
            user {
                email
                firstName
                lastName
            }
            success
            errors {
                field
                message
                code
            }
        }
    }
"""


def create_valid_telegram_init_data():
    """Create valid Telegram initDataRaw data"""
    # Construct data string
    user_data = {
        "id": 123456789,
        "first_name": "Test User",
        "last_name": "",
        "username": "testuser",
        "language_code": "en",
        "allows_write_to_pm": True,
    }

    data_dict = {
        "user": json.dumps(user_data),
        "auth_date": "1234567890",
        "chat_instance": "1234567890123456789",
        "chat_type": "private",
    }

    # Calculate HMAC signature
    data_string = urlencode(sorted(data_dict.items()))
    secret_key = hmac.new(
        b"test_bot_token_123456789", data_string.encode(), hashlib.sha256
    ).hexdigest()

    data_dict["hash"] = secret_key

    # Construct complete initDataRaw
    init_data_raw = urlencode(data_dict)
    return init_data_raw


@override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789")
@patch(
    "saleor.graphql.account.mutations.authentication.telegram_email_change_request.send_mail"
)
def test_telegram_email_change_request_success(mocked_send_mail, api_client):
    """Test successful Telegram email change request"""
    # Create test user
    user = User.objects.create_user(
        email="telegram_123456789@telegram.local",
        password="testpass123",
        first_name="Test",
        last_name="User",
        external_reference="telegram_123456789",
    )

    # Mock Telegram user data
    user_data = {
        "id": 123456789,
        "first_name": "Test User",
        "last_name": "",
        "username": "testuser",
        "language_code": "en",
        "allows_write_to_pm": True,
    }

    # Create valid initDataRaw
    init_data_raw = create_valid_telegram_init_data()

    variables = {
        "initDataRaw": init_data_raw,
        "oldEmail": "telegram_123456789@telegram.local",
        "newEmail": "newemail@example.com",
    }

    response = api_client.post_graphql(
        TELEGRAM_EMAIL_CHANGE_REQUEST_MUTATION, variables
    )
    content = get_graphql_content(response)

    data = content["data"]["telegramEmailChangeRequest"]

    # Verify no errors
    assert not data["errors"]

    # Verify user information returned
    assert data["user"]["email"] == "telegram_123456789@telegram.local"

    # Verify verification code returned
    assert data["verificationCode"] is not None
    assert len(data["verificationCode"]) == 6

    # Verify expiration time returned
    assert data["expiresAt"] is not None

    # Verify email was sent
    mocked_send_mail.assert_called_once()


@override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789")
def test_telegram_email_change_request_invalid_old_email(api_client):
    """Test invalid old email format"""
    # Create test user
    user = User.objects.create_user(
        email="telegram_123456789@telegram.local",
        password="testpass123",
        first_name="Test",
        last_name="User",
        external_reference="telegram_123456789",
    )

    init_data_raw = create_valid_telegram_init_data()

    variables = {
        "initDataRaw": init_data_raw,
        "oldEmail": "invalid@email.com",  # Invalid format
        "newEmail": "newemail@example.com",
    }

    response = api_client.post_graphql(
        TELEGRAM_EMAIL_CHANGE_REQUEST_MUTATION, variables
    )
    content = get_graphql_content(response)

    data = content["data"]["telegramEmailChangeRequest"]

    # Verify there are errors
    assert data["errors"]
    assert data["errors"][0]["field"] == "oldEmail"


@override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789")
def test_telegram_email_change_confirm_success(api_client):
    """Test successful Telegram email change confirmation"""
    # Create test user
    user = User.objects.create_user(
        email="telegram_123456789@telegram.local",
        password="testpass123",
        first_name="Test",
        last_name="User",
        external_reference="telegram_123456789",
    )

    # Store verification code in Redis (mock)
    verification_code = "123456"
    old_email = "telegram_123456789@telegram.local"
    new_email = "newemail@example.com"

    with patch(
        "saleor.graphql.account.mutations.authentication.telegram_email_change_confirm.get_redis_cache"
    ) as mock_redis:
        mock_redis.return_value.get.return_value = {
            "verification_code": verification_code,
            "old_email": old_email,
            "new_email": new_email,
            "telegram_id": 123456789,
            "user_id": user.pk,
            "created_at": "2024-01-01T00:00:00+00:00",
        }

        init_data_raw = create_valid_telegram_init_data()

        response = api_client.post_graphql(
            TELEGRAM_EMAIL_CHANGE_CONFIRM_MUTATION,
            variables={
                "initDataRaw": init_data_raw,
                "verificationCode": verification_code,
                "oldEmail": old_email,
                "newEmail": new_email,
            },
        )

    data = response.json()["data"]["telegramEmailChangeConfirm"]

    # Verify no errors
    assert not data["errors"]

    # Verify success
    assert data["success"] is True

    # Verify user email updated
    assert data["user"]["email"] == new_email

    # Verify token returned
    assert data["token"] is not None


@override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789")
def test_telegram_email_change_confirm_invalid_code(api_client):
    """Test invalid verification code"""
    # Create test user
    user = User.objects.create_user(
        email="telegram_123456789@telegram.local",
        password="testpass123",
        first_name="Test",
        last_name="User",
        external_reference="telegram_123456789",
    )

    # Store verification code in Redis (mock)
    verification_code = "123456"
    old_email = "telegram_123456789@telegram.local"
    new_email = "newemail@example.com"

    with patch(
        "saleor.graphql.account.mutations.authentication.telegram_email_change_confirm.get_redis_cache"
    ) as mock_redis:
        mock_redis.return_value.get.return_value = {
            "verification_code": verification_code,
            "old_email": old_email,
            "new_email": new_email,
            "telegram_id": 123456789,
            "user_id": user.pk,
            "created_at": "2024-01-01T00:00:00+00:00",
        }

        init_data_raw = create_valid_telegram_init_data()

        response = api_client.post_graphql(
            TELEGRAM_EMAIL_CHANGE_CONFIRM_MUTATION,
            variables={
                "initDataRaw": init_data_raw,
                "verificationCode": "wrong_code",  # Wrong code
                "oldEmail": old_email,
                "newEmail": new_email,
            },
        )

    data = response.json()["data"]["telegramEmailChangeConfirm"]

    # Verify there are errors
    assert data["errors"]
    assert data["errors"][0]["field"] == "verificationCode"


@pytest.fixture
def telegram_user():
    """Create test used Telegram user"""
    user = User.objects.create(
        email="telegram_123456@telegram.local",
        first_name="Test",
        last_name="User",
        external_reference="telegram_123456",
        is_active=True,
    )
    return user


@pytest.fixture
def mock_telegram_validation(monkeypatch):
    """Mock Telegram data validation"""

    def mock_validate_telegram_data(init_data_raw):
        return {
            "user": {
                "id": 123456,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
            }
        }

    monkeypatch.setattr(
        "saleor.graphql.account.mutations.authentication.telegram_token_create.validate_telegram_data",
        mock_validate_telegram_data,
    )


@pytest.fixture
def mock_send_email(monkeypatch):
    """Mock email sending"""

    def mock_send_mail(*args, **kwargs):
        return 1

    monkeypatch.setattr("django.core.mail.send_mail", mock_send_mail)


@pytest.fixture(autouse=True)
def clear_verification_codes():
    """Clear verification codes after each test"""
    yield
    with _verification_lock:
        _verification_codes.clear()


@pytest.mark.django_db
class TestTelegramEmailChange:
    def test_successful_telegram_email_change_request(self, api_client):
        """Test successful Telegram email change request"""
        # Create test user
        user = User.objects.create_user(
            email="telegram_123456789@telegram.local",
            password="testpass123",
            first_name="Test",
            last_name="User",
            external_reference="telegram_123456789",
        )

        # Mock Telegram user data
        user_data = {
            "id": 123456789,
            "first_name": "Test User",
            "last_name": "",
            "username": "testuser",
            "language_code": "en",
            "allows_write_to_pm": True,
        }

        # Create valid initDataRaw
        init_data_raw = create_valid_telegram_init_data()

        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
            with patch(
                "saleor.graphql.account.mutations.authentication.telegram_email_change_request.send_mail"
            ) as mocked_send_mail:
                response = api_client.post_graphql(
                    """
                    mutation TelegramEmailChangeRequest(
                        $initDataRaw: String!
                        $oldEmail: String!
                        $newEmail: String!
                    ) {
                        telegramEmailChangeRequest(
                            initDataRaw: $initDataRaw
                            oldEmail: $oldEmail
                            newEmail: $newEmail
                        ) {
                            user {
                                email
                                firstName
                                lastName
                            }
                            verificationCode
                            expiresAt
                            errors {
                                field
                                message
                                code
                            }
                        }
                    }
                    """,
                    variables={
                        "initDataRaw": init_data_raw,
                        "oldEmail": "telegram_123456789@telegram.local",
                        "newEmail": "newemail@example.com",
                    },
                )

        data = response.json()["data"]["telegramEmailChangeRequest"]

        # Verify no errors
        assert not data["errors"]

        # Verify user information returned
        assert data["user"]["email"] == "telegram_123456789@telegram.local"

        # Verify verification code returned
        assert data["verificationCode"] is not None
        assert len(data["verificationCode"]) == 6

        # Verify expiration time returned
        assert data["expiresAt"] is not None

        # Verify email was sent
        mocked_send_mail.assert_called_once()

    def test_invalid_old_email_format(self, api_client):
        """Test invalid old email format"""
        # Create test user
        user = User.objects.create_user(
            email="telegram_123456789@telegram.local",
            password="testpass123",
            first_name="Test",
            last_name="User",
            external_reference="telegram_123456789",
        )

        init_data_raw = create_valid_telegram_init_data()

        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
            response = api_client.post_graphql(
                """
                mutation TelegramEmailChangeRequest(
                    $initDataRaw: String!
                    $oldEmail: String!
                    $newEmail: String!
                ) {
                    telegramEmailChangeRequest(
                        initDataRaw: $initDataRaw
                        oldEmail: $oldEmail
                        newEmail: $newEmail
                    ) {
                        user {
                            email
                            firstName
                            lastName
                        }
                        verificationCode
                        expiresAt
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={
                    "initDataRaw": init_data_raw,
                    "oldEmail": "invalid@email.com",  # Invalid format
                    "newEmail": "newemail@example.com",
                },
            )

        data = response.json()["data"]["telegramEmailChangeRequest"]

        # Verify there are errors
        assert data["errors"]
        assert data["errors"][0]["field"] == "oldEmail"

    def test_successful_telegram_email_change_confirm(self, api_client):
        """Test successful Telegram email change confirmation"""
        # Create test user
        user = User.objects.create_user(
            email="telegram_123456789@telegram.local",
            password="testpass123",
            first_name="Test",
            last_name="User",
            external_reference="telegram_123456789",
        )

        # Store verification code in Redis (mock)
        verification_code = "123456"
        old_email = "telegram_123456789@telegram.local"
        new_email = "newemail@example.com"

        with patch(
            "saleor.graphql.account.mutations.authentication.telegram_email_change_confirm.get_redis_cache"
        ) as mock_redis:
            mock_redis.return_value.get.return_value = {
                "verification_code": verification_code,
                "old_email": old_email,
                "new_email": new_email,
                "telegram_id": 123456789,
                "user_id": user.pk,
                "created_at": "2024-01-01T00:00:00+00:00",
            }

            init_data_raw = create_valid_telegram_init_data()

            response = api_client.post_graphql(
                TELEGRAM_EMAIL_CHANGE_CONFIRM_MUTATION,
                variables={
                    "initDataRaw": init_data_raw,
                    "verificationCode": verification_code,
                    "oldEmail": old_email,
                    "newEmail": new_email,
                },
            )

        data = response.json()["data"]["telegramEmailChangeConfirm"]

        # Verify no errors
        assert not data["errors"]

        # Verify success
        assert data["success"] is True

        # Verify user email updated
        assert data["user"]["email"] == new_email

        # Verify token returned
        assert data["token"] is not None

    def test_invalid_verification_code(self, api_client):
        """Test invalid verification code"""
        # Create test user
        user = User.objects.create_user(
            email="telegram_123456789@telegram.local",
            password="testpass123",
            first_name="Test",
            last_name="User",
            external_reference="telegram_123456789",
        )

        # Store verification code in Redis (mock)
        verification_code = "123456"
        old_email = "telegram_123456789@telegram.local"
        new_email = "newemail@example.com"

        with patch(
            "saleor.graphql.account.mutations.authentication.telegram_email_change_confirm.get_redis_cache"
        ) as mock_redis:
            mock_redis.return_value.get.return_value = {
                "verification_code": verification_code,
                "old_email": old_email,
                "new_email": new_email,
                "telegram_id": 123456789,
                "user_id": user.pk,
                "created_at": "2024-01-01T00:00:00+00:00",
            }

            init_data_raw = create_valid_telegram_init_data()

            response = api_client.post_graphql(
                TELEGRAM_EMAIL_CHANGE_CONFIRM_MUTATION,
                variables={
                    "initDataRaw": init_data_raw,
                    "verificationCode": "wrong_code",  # Wrong code
                    "oldEmail": old_email,
                    "newEmail": new_email,
                },
            )

        data = response.json()["data"]["telegramEmailChangeConfirm"]

        # Verify there are errors
        assert data["errors"]
        assert data["errors"][0]["field"] == "verificationCode"


class TestCleanupExpiredCodes:
    """Test expired verification code cleanup functionality"""

    def test_cleanup_expired_codes(self):
        """Test cleanup expired verification codes"""
        # Clear existing data
        with _verification_lock:
            _verification_codes.clear()

        # Add some test data
        current_time = timezone.now()

        # Valid verification code
        valid_key = "email_change_verification:123"
        valid_data = {
            "verification_code": "123456",
            "new_email": "valid@example.com",
            "created_at": current_time.isoformat(),
            "expires_at": (current_time + timedelta(minutes=10)).isoformat(),
        }

        # Expired verification code
        expired_key = "email_change_verification:456"
        expired_data = {
            "verification_code": "654321",
            "new_email": "expired@example.com",
            "created_at": current_time.isoformat(),
            "expires_at": (current_time - timedelta(minutes=1)).isoformat(),
        }

        # Store data
        with _verification_lock:
            _verification_codes[valid_key] = valid_data
            _verification_codes[expired_key] = expired_data

        # Execute cleanup
        cleanup_expired_codes()

        # Verify result
        with _verification_lock:
            assert valid_key in _verification_codes
            assert expired_key not in _verification_codes
            assert len(_verification_codes) == 1
