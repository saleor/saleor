import pytest

from ..utils import assign_permissions
from .utils import create_staff, update_staff


@pytest.mark.e2e
def test_create_and_update_staff_with_metadata_core_1515(
    e2e_staff_api_client,
    permission_manage_staff,
):
    # Before
    permissions = [
        permission_manage_staff,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # Step 1 - Create staff member with metadata
    metadata = [{"key": "code", "value": "abc"}]
    private_metadata = [{"key": "priv_code", "value": "priv_abc"}]
    input_data = {
        "firstName": "Leo",
        "lastName": "Test",
        "email": "new_staff@saleor.com",
        "isActive": True,
        "metadata": metadata,
        "privateMetadata": private_metadata,
    }
    data = create_staff(
        e2e_staff_api_client,
        input_data,
    )

    assert data is not None
    staff_id = data["id"]
    assert staff_id is not None
    assert data["metadata"] == metadata
    assert data["privateMetadata"] == private_metadata

    # Step 2 - Update staff metadata
    updated_metadata = [{"key": "code", "value": "update_pub"}]
    updated_private_metadata = [{"key": "priv_code", "value": "update_priv"}]
    update_input = {
        "metadata": updated_metadata,
        "privateMetadata": updated_private_metadata,
    }
    data = update_staff(
        e2e_staff_api_client,
        staff_id,
        update_input,
    )
    assert data["id"] == staff_id
    assert data["metadata"] == updated_metadata
    assert data["privateMetadata"] == updated_private_metadata
