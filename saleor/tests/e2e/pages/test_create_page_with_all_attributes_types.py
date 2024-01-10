import datetime
import json

import pytest
import pytz
from django.conf import settings

from ....tests.utils import dummy_editorjs
from ..attributes.utils import prepare_all_attributes
from ..pages.utils import create_page, create_page_type
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions


@pytest.mark.e2e
def test_create_page_with_each_of_attribute_types_core_0701(
    e2e_staff_api_client,
    permission_manage_page_types_and_attributes,
    permission_manage_pages,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    site_settings,
):
    # Before
    permissions = [
        permission_manage_page_types_and_attributes,
        permission_manage_pages,
        *shop_permissions,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]

    (
        product_id,
        _product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        23,
    )

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
    ) = prepare_all_attributes(
        e2e_staff_api_client,
        attribute_type="PAGE_TYPE",
        entity_type="PRODUCT",
    )

    # Step 1 - Create page type with all attributes
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
    page_type_data = create_page_type(e2e_staff_api_client, "Page Type", add_attributes)
    page_type_id = page_type_data["id"]
    assert page_type_data["name"] == "Page Type"
    assert len(page_type_data["attributes"]) == 11

    # Step 2 - Create page with all attributes
    expected_base_text = "Test rich attribute text"
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))

    new_value = "new_test_value.txt"
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}{new_value}"
    file_content_type = "text/plain"

    attributes = [
        {"id": attr_dropdown_id, "values": ["Freddy Torres"]},
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
        {"id": attr_reference_id, "references": [product_id]},
        {"id": attr_file_id, "file": file_url, "contentType": file_content_type},
    ]

    page = create_page(
        e2e_staff_api_client,
        page_type_id,
        title="test Page",
        is_published=True,
        attributes=attributes,
    )
    assert page["title"] == "test Page"
    assert page["isPublished"] is True
    attributes = page["attributes"]
    assert len(attributes) == 11
