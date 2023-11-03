import datetime

import pytest
import pytz

from ..attributes.utils import attribute_create
from ..pages.utils import create_page, create_page_type
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions


def prepare_attributes(e2e_staff_api_client):
    # Dropdown
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
        values=values,
    )

    attr_dropdown_id = attr_dropdown["id"]

    # Multiselect
    values = [
        {"name": "Security"},
        {"name": "Support"},
        {"name": "Medical"},
        {"name": "General"},
    ]

    attr_multi = attribute_create(
        e2e_staff_api_client,
        input_type="MULTISELECT",
        name="Department",
        slug="department",
        type="PAGE_TYPE",
        value_required=True,
        values=values,
    )

    attr_multiselect_id = attr_multi["id"]

    # Date
    attr_date = attribute_create(
        e2e_staff_api_client,
        input_type="DATE",
        name="Date",
        slug="date",
        type="PAGE_TYPE",
        value_required=True,
    )

    attr_date_id = attr_date["id"]

    # Date time
    attr_date_time = attribute_create(
        e2e_staff_api_client,
        input_type="DATE_TIME",
        name="Date time",
        slug="date-time",
        type="PAGE_TYPE",
        value_required=True,
    )

    attr_date_time_id = attr_date_time["id"]

    # Plain text
    attr_plain_text = attribute_create(
        e2e_staff_api_client,
        input_type="PLAIN_TEXT",
        name="Plain text test",
        slug="plain-text-test",
        type="PAGE_TYPE",
        value_required=True,
    )

    attr_plain_text_id = attr_plain_text["id"]

    # Rich text
    attr_rich_text = attribute_create(
        e2e_staff_api_client,
        input_type="RICH_TEXT",
        name="Rich text test",
        slug="rich-text-test",
        type="PAGE_TYPE",
        value_required=True,
    )

    attr_rich_text_id = attr_rich_text["id"]

    # Numeric
    attr_numeric = attribute_create(
        e2e_staff_api_client,
        input_type="NUMERIC",
        name="Numeric test",
        slug="numeric-test",
        type="PAGE_TYPE",
        value_required=True,
        unit="G",
    )

    attr_numeric_id = attr_numeric["id"]

    # Boolean
    attr_bool = attribute_create(
        e2e_staff_api_client,
        input_type="BOOLEAN",
        name="Bool test",
        slug="bool-test",
        type="PAGE_TYPE",
        value_required=True,
    )

    attr_bool_id = attr_bool["id"]

    # Swatch
    values = [
        {"name": "black", "value": "#000000"},
        {"name": "blue", "value": "#4167E7"},
    ]

    attr_swatch = attribute_create(
        e2e_staff_api_client,
        input_type="SWATCH",
        name="Swatch test",
        slug="swatch-test",
        type="PAGE_TYPE",
        value_required=True,
        values=values,
    )

    attr_swatch_id = attr_swatch["id"]

    # Reference
    attr_reference = attribute_create(
        e2e_staff_api_client,
        input_type="REFERENCE",
        name="Reference test",
        slug="reference-test",
        type="PAGE_TYPE",
        value_required=True,
        entityType="PRODUCT",
    )

    attr_reference_id = attr_reference["id"]

    return (
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
    )


@pytest.mark.e2e
def test_order_cancel_fulfillment_core_0220(
    e2e_staff_api_client,
    permission_manage_page_types_and_attributes,
    permission_manage_pages,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    permissions = [
        permission_manage_page_types_and_attributes,
        permission_manage_pages,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        warehouse_id,
        channel_id,
        _channel_slug,
        _shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

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
    ) = prepare_attributes(e2e_staff_api_client)

    # Step 1 - Create page type with attributes
    page_type_data = create_page_type(
        e2e_staff_api_client,
        add_attributes=[
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
        ],
    )
    page_type_id = page_type_data["id"]

    # Step 2 - Create page
    attributes = [
        {"id": attr_dropdown_id, "values": ["Freddy Torres"]},
        {"id": attr_multiselect_id, "values": ["security", "support"]},
        {"id": attr_date_id, "date": "2021-01-01"},
        {
            "id": attr_date_time_id,
            "dateTime": datetime.datetime(2023, 1, 1, tzinfo=pytz.utc),
        },
        {"id": attr_plain_text_id, "plainText": "test plain text"},
        {
            "id": attr_rich_text_id,
            "richText": '{"time":1698938932209,"blocks":[{"id":"H3Dbv2kCI0","type":"header","data":{"text":"Hader","level":1}},{"id":"qLU4d0pmTT","type":"list","data":{"style":"ordered","items":["item1","item2","item2"]}}],"version":"2.24.3"}',
        },
        {"id": attr_numeric_id, "numeric": 10},
        {"id": attr_bool_id, "boolean": True},
        {"id": attr_swatch_id, "values": ["blue"]},
        {"id": attr_reference_id, "references": [product_id]},
    ]
    page = create_page(
        e2e_staff_api_client,
        page_type_id,
        title="test Page",
        is_published=True,
        attributes=attributes,
    )
    assert page["title"] == "test Page"
