import pytest

from ..attributes.utils import attribute_create, attribute_update
from ..pages.utils import create_page, create_page_type
from ..utils import assign_permissions
from .utils import (
    create_category,
    create_product,
    create_product_type,
    create_product_variant,
    raw_create_product,
    update_product,
)


@pytest.mark.e2e
def test_product_with_restricted_reference_attribute(
    e2e_staff_api_client,
    permission_manage_page_types_and_attributes,
    permission_manage_pages,
    permission_manage_products,
    permission_manage_product_types_and_attributes,
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

    product_type_data = create_product_type(
        e2e_staff_api_client,
        slug="product-type",
    )
    product_type_id = product_type_data["id"]

    # Step 1 - Create reference attributes with reference types
    page_reference_attribute_data = attribute_create(
        e2e_staff_api_client,
        input_type="REFERENCE",
        entity_type="PAGE",
        name="page ref",
        slug="page-ref",
        reference_types=[page_type_id],
    )
    page_ref_attribute_id = page_reference_attribute_data["id"]
    assert page_reference_attribute_data["entityType"] == "PAGE"
    assert len(page_reference_attribute_data["referenceTypes"]) == 1
    assert page_reference_attribute_data["referenceTypes"][0]["id"] == page_type_id
    assert (
        page_reference_attribute_data["referenceTypes"][0]["__typename"] == "PageType"
    )

    product_reference_attribute_data = attribute_create(
        e2e_staff_api_client,
        input_type="REFERENCE",
        entity_type="PRODUCT",
        name="product ref",
        slug="product-ref",
        reference_types=[product_type_id],
    )
    product_ref_attribute_id = product_reference_attribute_data["id"]
    assert product_reference_attribute_data["entityType"] == "PRODUCT"
    assert len(product_reference_attribute_data["referenceTypes"]) == 1
    assert (
        product_reference_attribute_data["referenceTypes"][0]["id"] == product_type_id
    )
    assert (
        product_reference_attribute_data["referenceTypes"][0]["__typename"]
        == "ProductType"
    )

    variant_reference_attribute_data = attribute_create(
        e2e_staff_api_client,
        input_type="SINGLE_REFERENCE",
        entity_type="PRODUCT_VARIANT",
        name="variant ref",
        slug="variant-ref",
        reference_types=[product_type_id],
    )
    variant_ref_attribute_id = variant_reference_attribute_data["id"]
    assert variant_reference_attribute_data["entityType"] == "PRODUCT_VARIANT"
    assert len(product_reference_attribute_data["referenceTypes"]) == 1
    assert (
        variant_reference_attribute_data["referenceTypes"][0]["id"] == product_type_id
    )
    assert (
        variant_reference_attribute_data["referenceTypes"][0]["__typename"]
        == "ProductType"
    )

    # Step 2 - Create product type with the attributes
    product_type_with_references = create_product_type(
        e2e_staff_api_client,
        "referenced-product-type",
        product_attributes=[
            page_ref_attribute_id,
            product_ref_attribute_id,
            variant_ref_attribute_id,
        ],
    )
    product_type_with_references_id = product_type_with_references["id"]
    assert len(product_type_with_references["productAttributes"]) == 3

    # Step 3 - Prepare references not valid for specified attributes
    page_type_data = create_page_type(e2e_staff_api_client, name="another page type")
    page_type_id_not_in_choices = page_type_data["id"]
    page_not_in_choices = create_page(
        e2e_staff_api_client, page_type_id_not_in_choices, title="invalid page"
    )
    page_not_in_choices_id = page_not_in_choices["id"]

    product_type_data = create_product_type(
        e2e_staff_api_client, slug="another-product-type"
    )
    product_type_id_not_in_choices = product_type_data["id"]
    product_not_in_choices = create_product(
        e2e_staff_api_client,
        product_type_id_not_in_choices,
        category_id,
        product_name="invalid product",
    )
    product_not_in_choices_id = product_not_in_choices["id"]
    variant_not_in_choices = create_product_variant(
        e2e_staff_api_client, product_not_in_choices_id
    )
    variant_id_not_in_choices = variant_not_in_choices["id"]

    # Step 4 - Create product with a wrong attribute value and check for error
    invalid_attribute_data = [
        {"id": page_ref_attribute_id, "references": [page_not_in_choices_id]},
        {"id": product_ref_attribute_id, "references": [product_not_in_choices_id]},
        {"id": variant_ref_attribute_id, "reference": variant_id_not_in_choices},
    ]
    product_content = raw_create_product(
        e2e_staff_api_client,
        product_type_with_references_id,
        category_id,
        attributes=invalid_attribute_data,
    )
    product_data = product_content["data"]["productCreate"]
    errors = product_data["errors"]
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == "INVALID"
    assert len(errors[0]["attributes"]) == len(invalid_attribute_data)

    # Step 5 - Create product with a correct attribute values
    correct_page = create_page(e2e_staff_api_client, page_type_id)
    correct_page_id = correct_page["id"]

    correct_product_ref = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
        product_name="valid product",
    )
    correct_product_ref_id = correct_product_ref["id"]
    correct_variant_ref = create_product_variant(
        e2e_staff_api_client, correct_product_ref_id
    )
    correct_variant_ref_id = correct_variant_ref["id"]

    attributes = [
        {"id": page_ref_attribute_id, "references": [correct_page_id]},
        {"id": product_ref_attribute_id, "references": [correct_product_ref_id]},
        {"id": variant_ref_attribute_id, "reference": correct_variant_ref_id},
    ]
    product_data = create_product(
        e2e_staff_api_client,
        product_type_with_references_id,
        category_id,
        attributes=attributes,
        product_name="Tested product",
    )
    product_id = product_data["id"]
    assert len(product_data["attributes"]) == 3

    # Step 6 - Update attributes and clear reference types
    attribute_data = attribute_update(
        e2e_staff_api_client, page_ref_attribute_id, {"referenceTypes": []}
    )
    assert attribute_data["referenceTypes"] == []

    attribute_data = attribute_update(
        e2e_staff_api_client, product_ref_attribute_id, {"referenceTypes": []}
    )
    assert attribute_data["referenceTypes"] == []

    attribute_data = attribute_update(
        e2e_staff_api_client, variant_ref_attribute_id, {"referenceTypes": []}
    )
    assert attribute_data["referenceTypes"] == []

    # Step 7 - Update product with a previously wrong attribute value
    product_data = update_product(
        e2e_staff_api_client,
        product_id,
        {"attributes": invalid_attribute_data},
    )
    assert len(product_data["attributes"]) == len(invalid_attribute_data)
