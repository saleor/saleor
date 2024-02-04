import pytest

from ..utils import assign_permissions
from .utils import create_customer, customer_update


@pytest.mark.e2e
def test_create_and_update_customer_with_metadata_core_1514(
    e2e_staff_api_client,
    permission_manage_users,
):
    # Before
    permissions = [
        permission_manage_users,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # Step 1 - Create a customer with metadata
    email = "new3@com.com"
    metadata = [{"key": "customer_code", "value": "abc"}]
    private_metadata = [{"key": "priv_customer_code", "value": "priv_abc"}]
    user_data = create_customer(
        e2e_staff_api_client,
        email,
        metadata,
        private_metadata,
    )

    assert user_data is not None
    user_id = user_data["id"]
    assert user_id is not None
    assert user_data["metadata"] == metadata
    assert user_data["privateMetadata"] == private_metadata

    # Step 2 - Update customer's metadata
    updated_metadata = [{"key": "customer_code", "value": "update_abc"}]
    updated_private_metadata = [
        {"key": "priv_customer_code", "value": "update_privabc"}
    ]
    update_input = {
        "metadata": updated_metadata,
        "privateMetadata": updated_private_metadata,
    }
    data = customer_update(
        e2e_staff_api_client,
        user_id,
        update_input,
    )
    assert data["id"] == user_id
    assert data["metadata"] == updated_metadata
    assert data["privateMetadata"] == updated_private_metadata
