import json
import hmac
import hashlib
from urllib.parse import urlencode
import pytest
from django.test import override_settings
from saleor.account.models import User

from ......account.error_codes import AccountErrorCode
from ......core.jwt import JWT_ACCESS_TYPE, JWT_REFRESH_TYPE, jwt_decode
from .....tests.utils import get_graphql_content

TELEGRAM_TOKEN_CREATE_MUTATION = """
    mutation telegramTokenCreate($initDataRaw: String!) {
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
"""


def create_real_init_data():
    """Create real initDataRaw data for Telegram authentication test"""
    # Real initDataRaw data
    user_data = {
        "id": 7498813057,
        "first_name": "Justin",
        "username": "justin_lung",
        "language_code": "zh-hans",
    }
    data_dict = {
        "user": json.dumps(user_data),
        "auth_date": "1717740000",
        "chat_instance": "-1234567890123456789",
        "chat_type": "private",
    }
    data_string = urlencode(sorted(data_dict.items()))
    secret_key = hmac.new(
        b"8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA",
        data_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    data_dict["hash"] = secret_key
    init_data_raw = urlencode(data_dict)
    return init_data_raw


@pytest.mark.django_db
def test_telegram_token_create_with_real_data(api_client):
    """Test Telegram authentication using real data"""
    # Real initDataRaw data
    init_data_raw = create_real_init_data()
    with override_settings(
        TELEGRAM_BOT_TOKEN="8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    ):
        response = api_client.post_graphql(
            TELEGRAM_TOKEN_CREATE_MUTATION,
            variables={"initDataRaw": init_data_raw},
        )
    data = get_graphql_content(response)["data"]["telegramTokenCreate"]
    # Verify no errors
    assert not data["errors"]
    # Verify token returned
    assert data["token"] is not None
    # Verify user information
    user = data["user"]
    assert user["firstName"] == "Justin"
    assert user["email"].startswith("telegram_7498813057@telegram.local")
    # Verify JWT token
    assert len(data["token"]) > 100
    # Verify refresh token
    assert data["refreshToken"] is not None
    assert len(data["refreshToken"]) > 100


@pytest.mark.django_db
def test_telegram_token_create_existing_user_real_data(api_client):
    """Test existing user case (using real data)"""
    # Create existing user
    user = User.objects.create_user(
        email="telegram_7498813057@telegram.local",
        first_name="OldName",
        last_name="OldLast",
        external_reference="telegram_7498813057",
    )
    # Real initDataRaw data
    init_data_raw = create_real_init_data()
    with override_settings(
        TELEGRAM_BOT_TOKEN="8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    ):
        response = api_client.post_graphql(
            TELEGRAM_TOKEN_CREATE_MUTATION,
            variables={"initDataRaw": init_data_raw},
        )
    data = get_graphql_content(response)["data"]["telegramTokenCreate"]
    # Verify no errors
    assert not data["errors"]
    # Verify token returned
    assert data["token"] is not None
    # Verify user information (should be updated to new info)
    user = data["user"]
    assert user["firstName"] == "Justin"  # Should be updated to new name
    assert user["email"] == "telegram_7498813057@telegram.local"


@override_settings(TELEGRAM_BOT_TOKEN="wrong_bot_token")
def test_telegram_token_create_wrong_bot_token(api_client):
    """Test wrong bot token"""

    # Use real data but wrong bot token
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    variables = {"initDataRaw": real_init_data_raw}

    response = api_client.post_graphql(TELEGRAM_TOKEN_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    data = content["data"]["telegramTokenCreate"]

    # Verify there are errors
    assert data["errors"], "Expected errors for wrong bot token"
    assert data["errors"][0]["field"] == "initDataRaw"


def test_telegram_token_create_no_bot_token_real_data(api_client):
    """Test no bot token case (using real data)"""

    # Real initDataRaw data
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    variables = {"initDataRaw": real_init_data_raw}

    with override_settings(TELEGRAM_BOT_TOKEN=None):
        response = api_client.post_graphql(TELEGRAM_TOKEN_CREATE_MUTATION, variables)
        content = get_graphql_content(response)

    data = content["data"]["telegramTokenCreate"]

    # Verify there are errors
    assert data["errors"], "Expected errors for missing bot token"
    assert data["errors"][0]["field"] == "initDataRaw"
