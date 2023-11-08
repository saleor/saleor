import pytest

from ..utils import assign_permissions
from .utils import create_customer, customer_bulk_update


@pytest.mark.e2e
def test_should_bulk_update_customers_metadata_core_1513(
    e2e_staff_api_client,
    permission_manage_users,
):
    # Before
    permissions = [
        permission_manage_users,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # Step 1 - Create customers
    customer_ids = []
    for i in range(5):
        email = f"test_{i + 1}@saleor.io"
        user_data = create_customer(e2e_staff_api_client, email)
        user_id = user_data["id"]
        customer_ids.append(user_id)
        assert customer_ids is not None

    # Step 2 - Update customers' metadata in bulk
    error_policy = "IGNORE_FAILED"
    customer_updates = []
    for i in range(5):
        metadata_value = f"metadata_{i + 1}"
        private_metadata_value = f"private_metadata_{i + 1}"
        metadata = [{"key": "customer_code", "value": metadata_value}]
        private_metadata = [
            {"key": "priv_customer_code", "value": private_metadata_value}
        ]
        customer_updates.append(
            {
                "id": customer_ids[i],
                "input": {
                    "metadata": metadata,
                    "privateMetadata": private_metadata,
                },
            }
        )

    data = customer_bulk_update(
        e2e_staff_api_client,
        customer_updates,
        error_policy,
    )

    assert "count" in data
    assert "results" in data
    assert len(data["results"]) == 5

    for i in range(5):
        user_id = data["results"][i]["customer"]["id"]
        updated_metadata = data["results"][i]["customer"]["metadata"]
        updated_private_metadata = data["results"][i]["customer"]["privateMetadata"]

        assert user_id == customer_ids[i]
        assert updated_metadata == customer_updates[i]["input"]["metadata"]
        assert (
            updated_private_metadata == customer_updates[i]["input"]["privateMetadata"]
        )
