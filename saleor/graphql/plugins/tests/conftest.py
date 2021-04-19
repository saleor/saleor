import pytest


@pytest.fixture
def staff_api_client_can_manage_plugins(staff_api_client, permission_manage_plugins):
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    return staff_api_client
