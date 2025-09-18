from typing import Union

from django.db.models import QuerySet, Value

from ..attribute import AttributeInputType
from ..core.postgres import NoValidationSearchVector
from ..core.utils.editorjs import clean_editor_js
from .models import Attribute, AttributeValue


def get_search_vectors_for_attribute_values(
    attribute: Attribute,
    values: Union[list, "QuerySet"],
    page_id_to_title_map: dict[int, str] | None = None,
    weight: str = "B",
) -> list[NoValidationSearchVector]:
    search_vectors = []

    input_type = attribute.input_type
    if input_type in [AttributeInputType.DROPDOWN, AttributeInputType.MULTISELECT]:
        search_vectors += [
            NoValidationSearchVector(Value(value.name), config="simple", weight=weight)
            for value in values
        ]
    elif input_type == AttributeInputType.RICH_TEXT:
        search_vectors += [
            NoValidationSearchVector(
                Value(clean_editor_js(value.rich_text, to_string=True)),
                config="simple",
                weight=weight,
            )
            for value in values
        ]
    elif input_type == AttributeInputType.PLAIN_TEXT:
        search_vectors += [
            NoValidationSearchVector(
                Value(value.plain_text), config="simple", weight=weight
            )
            for value in values
        ]
    elif input_type == AttributeInputType.NUMERIC:
        unit = attribute.unit
        search_vectors += [
            NoValidationSearchVector(
                Value(value.name + " " + unit if unit else value.name),
                config="simple",
                weight=weight,
            )
            for value in values
        ]
    elif input_type in [AttributeInputType.DATE, AttributeInputType.DATE_TIME]:
        search_vectors += [
            NoValidationSearchVector(
                Value(value.date_time.strftime("%Y-%m-%d %H:%M:%S")),
                config="simple",
                weight=weight,
            )
            for value in values
        ]
    elif input_type in [
        AttributeInputType.REFERENCE,
        AttributeInputType.SINGLE_REFERENCE,
    ]:
        # for now only AttributeEntityType.PAGE is supported
        search_vectors += [
            NoValidationSearchVector(
                Value(
                    get_reference_attribute_search_value(
                        value, page_id_to_title_map=page_id_to_title_map
                    )
                ),
                config="simple",
                weight=weight,
            )
            for value in values
            if value.reference_page_id is not None
        ]
    return search_vectors


def get_reference_attribute_search_value(
    attribute_value: AttributeValue, page_id_to_title_map: dict[int, str] | None = None
) -> str:
    """Get search value for reference attribute."""
    if attribute_value.reference_page_id:
        if page_id_to_title_map:
            return page_id_to_title_map.get(attribute_value.reference_page_id, "")
        return (
            attribute_value.reference_page.title
            if attribute_value.reference_page
            else ""
        )
    return ""
