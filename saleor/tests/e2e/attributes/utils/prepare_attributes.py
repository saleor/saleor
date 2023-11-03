from .create_attribute import attribute_create


def prepare_all_attributes(e2e_staff_api_client, attribute_type):
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

    # File
    attr_file = attribute_create(
        e2e_staff_api_client,
        input_type="FILE",
        name="File test",
        slug="file-test",
        type="PAGE_TYPE",
        value_required=False,
    )

    attr_file_id = attr_file["id"]

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
        attr_file_id,
    )
