import pytest
from django.test import override_settings

from ..channel.utils import create_channel
from ..utils import assign_permissions
from .utils import account_register


@override_settings(ALLOWED_CLIENT_HOSTS=["localhost"])
@pytest.mark.e2e
def test_should_create_account_without_email_confirmation_core_1502(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_channels,
):
    assign_permissions(e2e_staff_api_client, [permission_manage_channels])
    chanel_data = create_channel(e2e_staff_api_client)
    channel_slug = chanel_data["slug"]

    # Step 1 Create account for the new customer
    user_account = account_register(
        e2e_not_logged_api_client,
        "new-user@saleor.io",
        "password!",
        channel_slug,
    )

    assert user_account["id"] is not None
