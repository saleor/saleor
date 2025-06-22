import json
import hashlib
import hmac
from unittest.mock import patch
from urllib.parse import urlencode

import pytest
from django.test import override_settings

from saleor.account.models import User
from saleor.graphql.account.mutations.authentication.telegram_token_create import (
    TelegramTokenCreate,
)


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


@pytest.mark.django_db
class TestTelegramTokenCreate:
    def test_successful_telegram_authentication(self, api_client):
        """Test successful Telegram authentication"""
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
            response = api_client.post_graphql(
                """
                mutation TelegramTokenCreate($initDataRaw: String!) {
                    telegramTokenCreate(initDataRaw: $initDataRaw) {
                        token
                        refreshToken
                        csrfToken
                        user {
                            email
                            firstName
                            lastName
                        }
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={"initDataRaw": init_data_raw},
            )

        data = response.json()["data"]["telegramTokenCreate"]

        # Verify no errors
        assert not data["errors"]

        # Verify token returned
        assert data["token"] is not None

        # Verify user information
        user = data["user"]
        assert user["firstName"] == "Test User"
        assert user["email"].startswith("telegram_123456789@telegram.local")

        # Verify JWT token
        assert len(data["token"]) > 100

        # Verify refresh token
        assert data["refreshToken"] is not None
        assert len(data["refreshToken"]) > 100

    def test_missing_bot_token(self, api_client):
        """Test case when bot token is not configured"""
        init_data_raw = create_valid_telegram_init_data()

        with override_settings(TELEGRAM_BOT_TOKEN=None):
            response = api_client.post_graphql(
                """
                mutation TelegramTokenCreate($initDataRaw: String!) {
                    telegramTokenCreate(initDataRaw: $initDataRaw) {
                        token
                        refreshToken
                        csrfToken
                        user {
                            email
                            firstName
                            lastName
                        }
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={"initDataRaw": init_data_raw},
            )

        data = response.json()["data"]["telegramTokenCreate"]

        # Verify there are errors
        assert data["errors"]
        assert data["errors"][0]["field"] == "initDataRaw"

    def test_invalid_signature(self, api_client):
        """Test invalid signature data"""
        # Create data with wrong bot token
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

        # Use wrong bot token to create data
        data_string = urlencode(sorted(data_dict.items()))
        secret_key = hmac.new(
            b"wrong_bot_token", data_string.encode(), hashlib.sha256
        ).hexdigest()

        data_dict["hash"] = secret_key
        init_data_raw = urlencode(data_dict)

        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
            response = api_client.post_graphql(
                """
                mutation TelegramTokenCreate($initDataRaw: String!) {
                    telegramTokenCreate(initDataRaw: $initDataRaw) {
                        token
                        refreshToken
                        csrfToken
                        user {
                            email
                            firstName
                            lastName
                        }
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={"initDataRaw": init_data_raw},
            )

        data = response.json()["data"]["telegramTokenCreate"]

        # Verify there are errors
        assert data["errors"]

    def test_missing_hash(self, api_client):
        """Test missing hash parameter"""
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
            # Missing hash
        }

        init_data_raw = urlencode(data_dict)

        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
            response = api_client.post_graphql(
                """
                mutation TelegramTokenCreate($initDataRaw: String!) {
                    telegramTokenCreate(initDataRaw: $initDataRaw) {
                        token
                        refreshToken
                        csrfToken
                        user {
                            email
                            firstName
                            lastName
                        }
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={"initDataRaw": init_data_raw},
            )

        data = response.json()["data"]["telegramTokenCreate"]

        # Verify there are errors
        assert data["errors"]

    def test_missing_user_data(self, api_client):
        """Test missing user data"""
        # Construct missing user data initDataRaw
        init_data_raw = "auth_date=1234567890&hash=test_hash"

        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
            response = api_client.post_graphql(
                """
                mutation TelegramTokenCreate($initDataRaw: String!) {
                    telegramTokenCreate(initDataRaw: $initDataRaw) {
                        token
                        refreshToken
                        csrfToken
                        user {
                            email
                            firstName
                            lastName
                        }
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={"initDataRaw": init_data_raw},
            )

        data = response.json()["data"]["telegramTokenCreate"]

        # Verify there are errors
        assert data["errors"]
        assert data["errors"][0]["field"] == "initDataRaw"
        assert "Missing user data" in data["errors"][0]["message"]

    def test_existing_user(self, api_client, settings):
        """Test existing user"""
        from .....account.models import User

        # Create existing user
        existing_user = User.objects.create_user(
            email="telegram_123456789@telegram.local",
            first_name="Existing",
            last_name="User",
            is_active=True,
            is_confirmed=True,
        )

        user_data = {"id": 123456789, "first_name": "Test", "last_name": "User"}

        init_data_raw = create_valid_telegram_init_data()

        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
            response = api_client.post_graphql(
                """
                mutation TelegramTokenCreate($initDataRaw: String!) {
                    telegramTokenCreate(initDataRaw: $initDataRaw) {
                        token
                        refreshToken
                        csrfToken
                        user {
                            email
                            firstName
                            lastName
                        }
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={"initDataRaw": init_data_raw},
            )

        data = response.json()["data"]["telegramTokenCreate"]

        # Verify no errors
        assert not data["errors"]

        # Verify token returned
        assert data["token"]

        # Verify user information (should update to new information)
        user = data["user"]
        assert user["email"] == "telegram_123456789@telegram.local"
        assert user["firstName"] == "Test"  # Should update to new name
        assert user["lastName"] == "User"

    def test_invalid_json(self, api_client):
        """Test invalid JSON data"""
        # Construct invalid JSON data
        init_data_raw = "user=invalid_json&auth_date=1234567890&hash=test_hash"

        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
            response = api_client.post_graphql(
                """
                mutation TelegramTokenCreate($initDataRaw: String!) {
                    telegramTokenCreate(initDataRaw: $initDataRaw) {
                        token
                        refreshToken
                        csrfToken
                        user {
                            email
                            firstName
                            lastName
                        }
                        errors {
                            field
                            message
                            code
                        }
                    }
                }
                """,
                variables={"initDataRaw": init_data_raw},
            )

        data = response.json()["data"]["telegramTokenCreate"]

        # Verify there are errors
        assert data["errors"]
        assert data["errors"][0]["field"] == "initDataRaw"
        assert "Invalid JSON" in data["errors"][0]["message"]
