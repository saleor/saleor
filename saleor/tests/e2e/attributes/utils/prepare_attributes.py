from .attribute_bulk_create import bulk_create_attributes
from .create_attribute import attribute_create


def prepare_all_attributes(e2e_staff_api_client, attribute_type, entity_type):
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
        type=attribute_type,
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
        type=attribute_type,
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
        type=attribute_type,
        value_required=True,
    )

    attr_date_id = attr_date["id"]

    # Date time
    attr_date_time = attribute_create(
        e2e_staff_api_client,
        input_type="DATE_TIME",
        name="Date time",
        slug="date-time",
        type=attribute_type,
        value_required=True,
    )

    attr_date_time_id = attr_date_time["id"]

    # Plain text
    attr_plain_text = attribute_create(
        e2e_staff_api_client,
        input_type="PLAIN_TEXT",
        name="Plain text test",
        slug="plain-text-test",
        type=attribute_type,
        value_required=True,
    )

    attr_plain_text_id = attr_plain_text["id"]

    # Rich text
    attr_rich_text = attribute_create(
        e2e_staff_api_client,
        input_type="RICH_TEXT",
        name="Rich text test",
        slug="rich-text-test",
        type=attribute_type,
        value_required=True,
    )

    attr_rich_text_id = attr_rich_text["id"]

    # Numeric
    attr_numeric = attribute_create(
        e2e_staff_api_client,
        input_type="NUMERIC",
        name="Numeric test",
        slug="numeric-test",
        type=attribute_type,
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
        type=attribute_type,
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
        type=attribute_type,
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
        type=attribute_type,
        value_required=True,
        entityType=entity_type,
    )

    attr_reference_id = attr_reference["id"]

    # File
    attr_file = attribute_create(
        e2e_staff_api_client,
        input_type="FILE",
        name="File test",
        slug="file-test",
        type=attribute_type,
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


def prepare_all_attributes_in_bulk(e2e_staff_api_client, attribute_type, entity_type):
    attributes = [
        {
            "name": "Dropdown",
            "slug": "dropdown",
            "inputType": "DROPDOWN",
            "type": attribute_type,
            "valueRequired": True,
            "values": [
                {"name": "Freddy Torres"},
                {"name": "Isabella Smith"},
                {"name": "Hayden Blake"},
            ],
        },
        {
            "name": "Multiselect",
            "slug": "multiselect",
            "inputType": "MULTISELECT",
            "type": attribute_type,
            "valueRequired": True,
            "values": [
                {"name": "Security"},
                {"name": "Support"},
                {"name": "Medical"},
                {"name": "General"},
            ],
        },
        {
            "name": "Date",
            "slug": "date",
            "inputType": "DATE",
            "type": attribute_type,
            "valueRequired": True,
        },
        {
            "name": "Date time",
            "slug": "date-time",
            "inputType": "DATE_TIME",
            "type": attribute_type,
            "valueRequired": True,
        },
        {
            "name": "Plain text",
            "slug": "plain-text",
            "inputType": "PLAIN_TEXT",
            "type": attribute_type,
            "valueRequired": True,
        },
        {
            "name": "Rich text",
            "slug": "rich-text",
            "inputType": "RICH_TEXT",
            "type": attribute_type,
            "valueRequired": True,
        },
        {
            "name": "Numeric",
            "slug": "numeric",
            "inputType": "NUMERIC",
            "type": attribute_type,
            "valueRequired": True,
        },
        {
            "name": "Boolean",
            "slug": "boolean",
            "inputType": "BOOLEAN",
            "type": attribute_type,
            "valueRequired": True,
        },
        {
            "name": "Swatch",
            "slug": "swatch",
            "inputType": "SWATCH",
            "type": attribute_type,
            "valueRequired": True,
            "values": [
                {"name": "black", "value": "#000000"},
                {"name": "blue", "value": "#4167E7"},
            ],
        },
        {
            "name": "Reference",
            "slug": "reference",
            "inputType": "REFERENCE",
            "type": attribute_type,
            "valueRequired": False,
            "entityType": entity_type,
        },
        {
            "name": "File",
            "slug": "file",
            "inputType": "FILE",
            "type": attribute_type,
            "valueRequired": False,
        },
    ]
    attributes_data = bulk_create_attributes(e2e_staff_api_client, attributes)

    attr_dropdown_id = attributes_data["results"][0]["attribute"]["id"]
    attr_multiselect_id = attributes_data["results"][1]["attribute"]["id"]
    attr_date_id = attributes_data["results"][2]["attribute"]["id"]
    attr_date_time_id = attributes_data["results"][3]["attribute"]["id"]
    attr_plain_text_id = attributes_data["results"][4]["attribute"]["id"]
    attr_rich_text_id = attributes_data["results"][5]["attribute"]["id"]
    attr_numeric_id = attributes_data["results"][6]["attribute"]["id"]
    attr_bool_id = attributes_data["results"][7]["attribute"]["id"]
    attr_swatch_id = attributes_data["results"][8]["attribute"]["id"]
    attr_reference_id = attributes_data["results"][9]["attribute"]["id"]
    attr_file_id = attributes_data["results"][10]["attribute"]["id"]

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
