import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, cast

from django.db.models import Model
from django.db.models.expressions import Exists, OuterRef
from django.utils.text import slugify

from ....attribute import AttributeEntityType, AttributeInputType
from ....attribute import models as attribute_models
from ....page import models as page_models
from ....product import models as product_models
from ...product.utils import get_used_attribute_values_for_variant

if TYPE_CHECKING:
    from ....attribute.models import Attribute

T_INSTANCE = product_models.Product | product_models.ProductVariant | page_models.Page
T_ERROR_DICT = dict[tuple[str, str], list]


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
    references: list[str] | list[page_models.Page] | None = None
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
    attributes_data: list[tuple["Attribute", AttrValuesInput]],
) -> bool:
    """Compare already assigned attribute values with values from AttrValuesInput.

    Return:
        `False` if the attribute values are equal, otherwise `True`.

    """
    if variant.product_id is not None:
        assigned_attributes = get_used_attribute_values_for_variant(variant)
        input_attribute_values: defaultdict[str, list[str]] = defaultdict(list)
        for attr, attr_data in attributes_data:
            values = get_values_from_attribute_values_input(attr, attr_data)
            if attr_data.global_id is not None:
                input_attribute_values[attr_data.global_id].extend(values)
        if input_attribute_values != assigned_attributes:
            return True
    return False


def get_values_from_attribute_values_input(
    attribute: attribute_models.Attribute, attribute_data: AttrValuesInput
) -> list[str]:
    """Format attribute values of type FILE."""
    if attribute.input_type == AttributeInputType.FILE:
        return (
            [slugify(attribute_data.file_url.split("/")[-1])]
            if attribute_data.file_url
            else []
        )
    return attribute_data.values or []
