import datetime
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, cast

from django.db.models import Model
from django.db.models.expressions import Exists, OuterRef

from ....attribute import AttributeEntityType, AttributeInputType
from ....attribute import models as attribute_models
from ....page import models as page_models
from ....product import models as product_models
from ..enums import AttributeValueBulkActionEnum

if TYPE_CHECKING:
    from ....attribute.models import Attribute

T_INSTANCE = product_models.Product | product_models.ProductVariant | page_models.Page
T_ERROR_DICT = dict[tuple[str, str], list]
T_REFERENCE = (
    product_models.Product
    | product_models.ProductVariant
    | product_models.Category
    | product_models.Collection
    | page_models.Page
)


@dataclass
class AssignedAttributeData:
    attribute: attribute_models.Attribute
    channel_slug: str | None
    product_id: int | None = None
    page_id: int | None = None
    variant_id: int | None = None


@dataclass
class AttrValuesForSelectableFieldInput:
    id: str | None = None
    external_reference: str | None = None
    value: str | None = None


@dataclass
class AttrValuesInput:
    global_id: str | None
    external_reference: str | None = None
    values: list[str] | None = None
    dropdown: AttrValuesForSelectableFieldInput | None = None
    swatch: AttrValuesForSelectableFieldInput | None = None
    multiselect: list[AttrValuesForSelectableFieldInput] | None = None
    numeric: str | None = None
    reference: str | None = None
    references: list[str] | None = None
    reference_objects: list[T_REFERENCE] | None = None
    file_url: str | None = None
    content_type: str | None = None
    rich_text: dict | None = None
    plain_text: str | None = None
    boolean: bool | None = None
    date: datetime.date | None = None
    date_time: datetime.datetime | None = None


class EntityTypeData(NamedTuple):
    """Defines metadata for a referenceable entity type."""

    model: type[Model]
    name_field: str
    value_field: str


ENTITY_TYPE_MAPPING = {
    AttributeEntityType.PAGE: EntityTypeData(
        page_models.Page, "title", "reference_page"
    ),
    AttributeEntityType.PRODUCT: EntityTypeData(
        product_models.Product, "name", "reference_product"
    ),
    AttributeEntityType.PRODUCT_VARIANT: EntityTypeData(
        product_models.ProductVariant, "name", "reference_variant"
    ),
    AttributeEntityType.CATEGORY: EntityTypeData(
        product_models.Category, "name", "reference_category"
    ),
    AttributeEntityType.COLLECTION: EntityTypeData(
        product_models.Collection, "name", "reference_collection"
    ),
}


def get_assignment_model_and_fk(instance: T_INSTANCE):
    if isinstance(instance, page_models.Page):
        return attribute_models.AssignedPageAttributeValue, "page_id"
    if isinstance(instance, product_models.Product):
        return attribute_models.AssignedProductAttributeValue, "product_id"
    raise NotImplementedError(
        f"Assignment for {type(instance).__name__} not implemented."
    )


def get_assigned_attribute_value_if_exists(
    instance: T_INSTANCE, attribute: "Attribute", lookup_field: str, value
):
    """Unified method to find an existing assigned value."""
    if isinstance(instance, product_models.ProductVariant):
        # variant has old attribute structure so need to handle it differently
        return get_variant_assigned_attribute_value_if_exists(
            instance, attribute, lookup_field, value
        )

    assignment_model, instance_fk = get_assignment_model_and_fk(instance)
    assigned_values = assignment_model.objects.filter(**{instance_fk: instance.pk})
    return attribute_models.AttributeValue.objects.filter(
        Exists(assigned_values.filter(value_id=OuterRef("id"))),
        attribute_id=attribute.pk,
        **{lookup_field: value},
    ).first()


def get_variant_assigned_attribute_value_if_exists(
    instance: T_INSTANCE, attribute: "Attribute", lookup_field: str, value: str
):
    variant = cast(product_models.ProductVariant, instance)
    attribute_variant = Exists(
        attribute_models.AttributeVariant.objects.filter(
            pk=OuterRef("assignment_id"),
            attribute_id=attribute.pk,
        )
    )
    assigned_variant = Exists(
        attribute_models.AssignedVariantAttribute.objects.filter(
            attribute_variant
        ).filter(
            variant_id=variant.pk,
            values=OuterRef("pk"),
        )
    )
    return attribute_models.AttributeValue.objects.filter(
        assigned_variant, **{lookup_field: value}
    ).first()


def has_input_modified_attribute_values(
    variant: product_models.ProductVariant,
    pre_save_bulk_data: dict[
        AttributeValueBulkActionEnum, dict[attribute_models.Attribute, list]
    ],
) -> bool:
    """Compare already assigned attribute values with the input values.

    The change in the attribute values order is also considered a modification.

    Return:
        `False` if the attribute values are equal, otherwise `True`.

    """
    if variant.product_id is not None:
        assigned_attributes = get_attribute_to_values_map_for_variant(variant)
        input_attribute_values = get_values_from_pre_save_bulk_data(pre_save_bulk_data)
        if input_attribute_values != assigned_attributes:
            return True
    return False


def get_attribute_to_values_map_for_variant(
    variant: product_models.ProductVariant,
) -> dict[int, list]:
    """Create a dict of attributes values for variant.

    Sample result is:
    {
        "attribute_pk": [AttributeValue1, AttributeValue2],
        "attribute_pk": [AttributeValue3]
    }
    """
    attribute_values: defaultdict[int, list[str | None | datetime.datetime]] = (
        defaultdict(list)
    )
    for assigned_variant_attribute in variant.attributes.all():
        attribute = assigned_variant_attribute.attribute
        attribute_id = attribute.pk
        for attr_value in assigned_variant_attribute.values.all():
            if attribute.input_type == AttributeInputType.PLAIN_TEXT:
                attribute_values[attribute_id].append(attr_value.plain_text)
            elif attribute.input_type == AttributeInputType.RICH_TEXT:
                attribute_values[attribute_id].append(json.dumps(attr_value.rich_text))
            elif attribute.input_type == AttributeInputType.NUMERIC:
                attribute_values[attribute_id].append(str(attr_value.numeric))
            elif attribute.input_type in [
                AttributeInputType.DATE,
                AttributeInputType.DATE_TIME,
            ]:
                attribute_values[attribute_id].append(attr_value.date_time)
            else:
                attribute_values[attribute_id].append(attr_value.slug)
    return attribute_values


def get_values_from_pre_save_bulk_data(
    pre_save_bulk_data: dict[
        AttributeValueBulkActionEnum, dict[attribute_models.Attribute, list]
    ],
) -> dict[int, list[str | None | datetime.datetime]]:
    input_type_to_field_and_action = {
        AttributeInputType.PLAIN_TEXT: ("plain_text", None),
        AttributeInputType.RICH_TEXT: ("rich_text", json.dumps),
        AttributeInputType.NUMERIC: ("numeric", str),
        AttributeInputType.DATE: ("date_time", None),
        AttributeInputType.DATE_TIME: ("date_time", None),
    }
    input_attribute_values: defaultdict[int, list[str | None | datetime.datetime]] = (
        defaultdict(list)
    )
    for action, attributes in pre_save_bulk_data.items():
        for attr, values_data in attributes.items():
            values = []
            if action == AttributeValueBulkActionEnum.GET_OR_CREATE:
                values = [value["slug"] for value in values_data]
            elif action == AttributeValueBulkActionEnum.UPDATE_OR_CREATE:
                field_name, transform = input_type_to_field_and_action.get(
                    attr.input_type, (None, None)
                )
                if field_name:
                    values = [
                        transform(value["defaults"][field_name])
                        if transform
                        else value["defaults"][field_name]
                        for value in values_data
                    ]
            else:
                values = [value.slug for value in values_data]
            input_attribute_values[attr.pk].extend(values)
    return input_attribute_values
