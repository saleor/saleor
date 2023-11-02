import pytest

from ..attributes.utils import attribute_create
from ..pages.utils import create_page, create_page_type
from ..utils import assign_permissions


def prepare_attributes(e2e_staff_api_client):
    values = [
        {"name": "Freddy Torres"},
        {"name": "Isabella Smith"},
        {"name": "Hayden Blake"},
    ]
    attr_dropdown = attribute_create(
        e2e_staff_api_client,
        input_type="DROPDOWN",
        name="Author",
        slug="author",
        type="PAGE_TYPE",
        value_required=True,
        is_variant_only=False,
        values=values,
    )

    attr_dropdown_id = attr_dropdown["id"]
    return attr_dropdown_id


@pytest.mark.e2e
def test_order_cancel_fulfillment_core_0220(
    e2e_staff_api_client,
    permission_manage_page_types_and_attributes,
    permission_manage_pages,
):
    # Before
    permissions = [permission_manage_page_types_and_attributes, permission_manage_pages]
    assign_permissions(e2e_staff_api_client, permissions)

    attr_dropdown_id = prepare_attributes(e2e_staff_api_client)

    # Step 1 - Create page type with attributes
    page_type_data = create_page_type(
        e2e_staff_api_client, add_attributes=[attr_dropdown_id]
    )
    page_type_id = page_type_data["id"]

    # Step 2 - Create page
    attributes = [{"id": attr_dropdown_id, "values": ["dennis-perkins"]}]
    page = create_page(
        e2e_staff_api_client,
        page_type_id,
        title="test Page",
        is_published=True,
        attributes=attributes,
    )
    assert page["title"] == "test Page"
