from collections import defaultdict

import graphene
from django.utils.text import slugify
from text_unidecode import unidecode

from ...enums import AttributeValueBulkActionEnum
from ...utils.shared import AttrValuesInput
from ...utils.type_handlers import AttributeInputErrors, ReferenceAttributeHandler


def test_reference_handler_clean_and_validate_product_reference(
    product_type_product_reference_attribute, product_list
):
    # given
    product_ids = [graphene.Node.to_global_id("Product", p.id) for p in product_list]
    attribute = product_type_product_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=product_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.references
    assert handler.values_input.reference_objects
    assert set(handler.values_input.reference_objects) == set(product_list)


def test_reference_handler_clean_and_validate_page_reference(
    product_type_page_reference_attribute, page_list
):
    # given
    page_ids = [graphene.Node.to_global_id("Page", p.id) for p in page_list]
    attribute = product_type_page_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=page_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.references
    assert handler.values_input.reference_objects
    assert set(handler.values_input.reference_objects) == set(page_list)


def test_reference_handler_clean_and_validate_variant_reference(
    page_type_variant_reference_attribute, product_variant_list
):
    # given
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", v.id) for v in product_variant_list
    ]
    attribute = page_type_variant_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=variant_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.references
    assert handler.values_input.reference_objects
    assert set(handler.values_input.reference_objects) == set(product_variant_list)


def test_reference_handler_clean_and_validate_product_reference_with_reference_types(
    product_type_product_reference_attribute, product_list, product_type
):
    # given
    product_type_product_reference_attribute.reference_product_types.add(product_type)
    product_ids = [graphene.Node.to_global_id("Product", p.id) for p in product_list]
    attribute = product_type_product_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=product_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.references
    assert handler.values_input.reference_objects
    assert set(handler.values_input.reference_objects) == set(product_list)


def test_reference_handler_clean_and_validate_page_reference_with_reference_types(
    product_type_page_reference_attribute, page_list, page_type
):
    # given
    product_type_page_reference_attribute.reference_page_types.add(page_type)
    page_ids = [graphene.Node.to_global_id("Page", p.id) for p in page_list]
    attribute = product_type_page_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=page_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.references
    assert handler.values_input.reference_objects
    assert set(handler.values_input.reference_objects) == set(page_list)


def test_reference_handler_clean_and_validate_variant_reference_with_reference_types(
    page_type_variant_reference_attribute, product_variant_list, product_type
):
    # given
    page_type_variant_reference_attribute.reference_product_types.add(product_type)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", v.id) for v in product_variant_list
    ]
    attribute = page_type_variant_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=variant_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.references
    assert handler.values_input.reference_objects
    assert set(handler.values_input.reference_objects) == set(product_variant_list)


def test_reference_handler_clean_and_validate_category_reference(
    product_type_category_reference_attribute, category_list
):
    # given
    category_ids = [graphene.Node.to_global_id("Category", c.id) for c in category_list]
    attribute = product_type_category_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=category_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference_objects
    assert handler.values_input.references
    assert set(handler.values_input.reference_objects) == set(category_list)


def test_reference_handler_clean_and_validate_collection_reference(
    product_type_collection_reference_attribute, collection_list
):
    # given
    collection_ids = [
        graphene.Node.to_global_id("Collection", c.id) for c in collection_list
    ]
    attribute = product_type_collection_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, references=collection_ids)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.references
    assert handler.values_input.reference_objects
    assert set(handler.values_input.reference_objects) == set(collection_list)


def test_reference_handler_clean_and_validate_invalid_product_reference_type(
    product_type_product_reference_attribute,
    product,
    product_type_with_variant_attributes,
):
    # given
    attribute = product_type_product_reference_attribute
    product_type_product_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        references=[graphene.Node.to_global_id("Product", product.id)],
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE_TYPE]


def test_reference_handler_clean_and_validate_invalid_product_variant_ref_type(
    product_type_variant_reference_attribute,
    variant,
    product_type_with_variant_attributes,
):
    # given
    attribute = product_type_variant_reference_attribute
    product_type_variant_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        references=[graphene.Node.to_global_id("ProductVariant", variant.id)],
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE_TYPE]


def test_reference_handler_clean_and_validate_invalid_page_reference_type(
    product_type_page_reference_attribute, page, page_type_list
):
    # given
    attribute = product_type_page_reference_attribute
    product_type_page_reference_attribute.reference_page_types.add(page_type_list[1])
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        references=[graphene.Node.to_global_id("Page", page.id)],
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE_TYPE]


def test_single_reference_handler_clean_and_validate_page_reference(
    product_type_page_single_reference_attribute, page
):
    # given
    attribute = product_type_page_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    page_id = graphene.Node.to_global_id("Page", page.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=page_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference_objects == [page]


def test_single_reference_handler_clean_and_validate_variant_reference(
    product_type_variant_single_reference_attribute, variant
):
    # given
    attribute = product_type_variant_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=variant_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference_objects == [variant]


def test_single_reference_handler_clean_and_validate_category_reference(
    product_type_category_single_reference_attribute, category
):
    # given
    attribute = product_type_category_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=category_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference_objects == [category]


def test_single_reference_handler_clean_and_validate_collection_reference(
    page_type_collection_single_reference_attribute, collection
):
    # given
    attribute = page_type_collection_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=collection_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference_objects == [collection]


def test_single_reference_handler_clean_and_validate_product_ref_with_reference_types(
    product_type_product_single_reference_attribute, product, product_type
):
    # given
    product_type_product_single_reference_attribute.reference_product_types.add(
        product_type
    )
    product_id = graphene.Node.to_global_id("Product", product.id)
    attribute = product_type_product_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=product_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference
    assert handler.values_input.reference_objects == [product]


def test_single_reference_handler_clean_and_validate_page_ref_with_reference_types(
    product_type_page_single_reference_attribute, page, page_type
):
    # given
    product_type_page_single_reference_attribute.reference_page_types.add(page_type)
    page_id = graphene.Node.to_global_id("Page", page.id)
    attribute = product_type_page_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=page_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference
    assert handler.values_input.reference_objects == [page]


def test_single_reference_handler_clean_and_validate_variant_ref_with_reference_types(
    page_type_variant_single_reference_attribute, variant, product_type
):
    # given
    page_type_variant_single_reference_attribute.reference_product_types.add(
        product_type
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    attribute = page_type_variant_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=variant_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference
    assert handler.values_input.reference_objects == [variant]


def test_single_reference_handler_clean_and_validate_success(
    product_type_product_single_reference_attribute, product
):
    # given
    attribute = product_type_product_single_reference_attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
    values_input = AttrValuesInput(global_id=attribute_id, reference=product_id)
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert not attribute_errors
    assert handler.values_input.reference_objects == [product]


def test_reference_handler_clean_and_validate_value_required(
    product_type_product_reference_attribute,
):
    # given
    attribute = product_type_product_reference_attribute
    attribute.value_required = True
    attribute.save(update_fields=["value_required"])
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id), references=[]
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.REFERENCE_REQUIRED]


def test_single_reference_handlers_clean_and_validate_value_required(
    product_type_product_single_reference_attribute,
):
    # given
    attribute = product_type_product_single_reference_attribute
    attribute.value_required = True
    attribute.save(update_fields=["value_required"])
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id), reference=None
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.REFERENCE_REQUIRED]


def test_reference_handler_clean_and_validate_invalid_reference(
    product_type_product_reference_attribute, product
):
    # given
    attribute = product_type_product_reference_attribute
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        references=[
            graphene.Node.to_global_id("ProductVariant", product.id),
            graphene.Node.to_global_id("Product", "123"),
            "ABC",
        ],
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE]


def test_single_reference_handler_clean_and_validate_invalid_reference(
    product_type_product_single_reference_attribute, product
):
    # given
    attribute = product_type_product_single_reference_attribute
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        reference=graphene.Node.to_global_id("Order", product.id),
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE]


def test_single_reference_handler_clean_and_validate_invalid_product_reference_type(
    product_type_product_single_reference_attribute,
    product,
    product_type_with_variant_attributes,
):
    # given
    attribute = product_type_product_single_reference_attribute
    product_type_product_single_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        reference=graphene.Node.to_global_id("Product", product.id),
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE_TYPE]


def test_single_reference_handler_clean_and_validate_invalid_product_variant_ref_type(
    product_type_variant_single_reference_attribute,
    variant,
    product_type_with_variant_attributes,
):
    # given
    attribute = product_type_variant_single_reference_attribute
    product_type_variant_single_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        reference=graphene.Node.to_global_id("ProductVariant", variant.id),
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE_TYPE]


def test_single_reference_handler_clean_and_validate_invalid_page_reference_type(
    product_type_page_single_reference_attribute, page, page_type_list
):
    # given
    attribute = product_type_page_single_reference_attribute
    product_type_page_single_reference_attribute.reference_page_types.add(
        page_type_list[1]
    )
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        reference=graphene.Node.to_global_id("Page", page.id),
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    attribute_errors = defaultdict(list)

    # when
    handler.clean_and_validate(attribute_errors)

    # then
    assert attribute_errors[AttributeInputErrors.INVALID_REFERENCE_TYPE]


def test_reference_handler_pre_save_value(
    product_type_product_reference_attribute, product_list, product
):
    # given
    attribute = product_type_product_reference_attribute
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        reference_objects=product_list,
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    instance = product

    # when
    result = handler.pre_save_value(instance)

    # then
    assert len(result) == len(product_list)
    for i, ref_product in enumerate(product_list):
        action, value_data = result[i]
        expected_slug = slugify(unidecode(f"{instance.id}_{ref_product.id}"))

        assert action == AttributeValueBulkActionEnum.GET_OR_CREATE
        assert value_data["attribute"] == attribute
        assert value_data["slug"] == expected_slug
        assert value_data["defaults"]["name"] == ref_product.name
        assert value_data["reference_product"] == ref_product


def test_single_reference_handler_pre_save_value(
    product_type_product_single_reference_attribute, product_list, product
):
    # given
    attribute = product_type_product_single_reference_attribute
    ref_product = product_list[0]
    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", attribute.id),
        reference_objects=[ref_product],
    )
    handler = ReferenceAttributeHandler(attribute, values_input)
    instance = product

    # when
    result = handler.pre_save_value(instance)

    # then
    assert len(result) == 1
    action, value_data = result[0]
    expected_slug = slugify(unidecode(f"{instance.id}_{ref_product.id}"))

    assert action == AttributeValueBulkActionEnum.GET_OR_CREATE
    assert value_data["attribute"] == attribute
    assert value_data["slug"] == expected_slug
    assert value_data["defaults"]["name"] == ref_product.name
    assert value_data["reference_product"] == ref_product
