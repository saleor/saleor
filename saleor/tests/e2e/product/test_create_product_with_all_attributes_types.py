import datetime
import json

import pytest
import pytz
from django.conf import settings

from ....tests.utils import dummy_editorjs
from ..attributes.utils import prepare_all_attributes_in_bulk
from ..pages.utils import create_page, create_page_type
from ..utils import assign_permissions
from .utils import (
    create_category,
    create_product,
    create_product_type,
)


@pytest.mark.e2e
def test_create_product_with_attributes_created_in_bulk_core_0704(
    e2e_staff_api_client,
    permission_manage_page_types_and_attributes,
    permission_manage_pages,
    permission_manage_products,
    permission_manage_product_types_and_attributes,
    site_settings,
):
    # Before
    permissions = [
        permission_manage_page_types_and_attributes,
        permission_manage_pages,
        permission_manage_products,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]
    page_type_data = create_page_type(e2e_staff_api_client)
    page_type_id = page_type_data["id"]
    page_data = create_page(e2e_staff_api_client, page_type_id)
    page_id = page_data["id"]

    # Step 1 - Bulk create attributes for each input type
    (
        attr_dropdown_id,
        attr_multiselect_id,
        attr_date_id,
        attr_date_time_id,
        attr_plain_text_id,
        attr_rich_text_id,
        attr_numeric_id,
        attr_bool_id,
        attr_swatch_id,
        attr_reference_id,
        attr_file_id,
    ) = prepare_all_attributes_in_bulk(
        e2e_staff_api_client, attribute_type="PRODUCT_TYPE", entity_type="PAGE"
    )

    # Step 2 - Create product type with all attributes
    add_attributes = [
        attr_dropdown_id,
        attr_multiselect_id,
        attr_date_id,
        attr_date_time_id,
        attr_plain_text_id,
        attr_rich_text_id,
        attr_numeric_id,
        attr_bool_id,
        attr_swatch_id,
        attr_reference_id,
        attr_file_id,
    ]
    product_type_data = create_product_type(
        e2e_staff_api_client,
        slug="all-attributes-type",
        product_attributes=add_attributes,
    )
    product_type_id = product_type_data["id"]
    assert len(product_type_data["productAttributes"]) == 11

    # Step 3 - Create product with all attributes
    expected_base_text = "Test rich attribute text"
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))
    new_value = "new_test_value.txt"
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}{new_value}"
    file_content_type = "text/plain"

    attributes = [
        {"id": attr_dropdown_id, "dropdown": {"value": "Isabella Smith"}},
        {"id": attr_multiselect_id, "values": ["security", "support"]},
        {"id": attr_date_id, "date": "2021-01-01"},
        {
            "id": attr_date_time_id,
            "dateTime": datetime.datetime(2023, 1, 1, tzinfo=pytz.utc),
        },
        {"id": attr_plain_text_id, "plainText": "test plain text"},
        {"id": attr_rich_text_id, "richText": expected_rich_text},
        {"id": attr_numeric_id, "numeric": 10},
        {"id": attr_bool_id, "boolean": True},
        {"id": attr_swatch_id, "values": ["blue"]},
        {"id": attr_reference_id, "references": [page_id]},
        {"id": attr_file_id, "file": file_url, "contentType": file_content_type},
    ]
    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
        attributes=attributes,
    )
    attributes = product_data["attributes"]
    assert len(product_data["attributes"]) == 11
