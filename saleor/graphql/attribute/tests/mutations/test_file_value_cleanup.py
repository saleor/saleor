from unittest import mock

import graphene
from django.conf import settings

from .....attribute import AttributeInputType, AttributeType
from .....attribute.models import (
    AssignedPageAttributeValue,
    AssignedProductAttributeValue,
    AssignedVariantAttributeValue,
    Attribute,
    AttributeValue,
)
from .....attribute.utils import associate_attribute_values_to_instance
from .....product.models import Product
from ....tests.utils import get_graphql_content

PRODUCT_UPDATE_MUTATION = """
    mutation ProductUpdate($productId: ID!, $input: ProductInput!) {
        productUpdate(id: $productId, input: $input) {
            errors {
                field
                code
                message
            }
        }
    }
"""

VARIANT_UPDATE_MUTATION = """
    mutation VariantUpdate($id: ID!, $attributes: [AttributeValueInput!]) {
        productVariantUpdate(id: $id, input: {attributes: $attributes}) {
            errors {
                field
                code
                message
            }
        }
    }
"""

VARIANT_BULK_UPDATE_MUTATION = """
    mutation VariantBulkUpdate(
        $productId: ID!, $variants: [ProductVariantBulkUpdateInput!]!
    ) {
        productVariantBulkUpdate(product: $productId, variants: $variants) {
            count
            results {
                errors {
                    field
                    code
                    message
                }
            }
        }
    }
"""

PAGE_UPDATE_MUTATION = """
    mutation PageUpdate($id: ID!, $attributes: [AttributeValueInput!]) {
        pageUpdate(id: $id, input: {attributes: $attributes}) {
            errors {
                field
                code
                message
            }
        }
    }
"""

CUSTOMER_UPDATE_MUTATION = """
    mutation CustomerUpdate($id: ID!, $attributes: [AttributeValueInput!]) {
        customerUpdate(id: $id, input: {attributes: $attributes}) {
            errors {
                field
                code
                message
            }
        }
    }
"""


def build_file_url(file_name):
    return f"https://example.com{settings.MEDIA_URL}{file_name}"


class RollbackTrigger(Exception):
    pass


def test_replace_deletes_previous_value(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
):
    # given
    product_type.product_attributes.add(file_attribute)
    old_value = file_attribute.values.first()
    unassigned_sibling_value = file_attribute.values.last()
    associate_attribute_values_to_instance(product, {file_attribute.pk: [old_value]})

    file_name = "new_file.jpg"
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                    "file": build_file_url(file_name),
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    new_value = AssignedProductAttributeValue.objects.get(
        product=product, value__attribute=file_attribute
    ).value
    assert new_value.file_url == file_name

    # ensure sibling vales is untouched
    assert AttributeValue.objects.filter(pk=unassigned_sibling_value.pk).exists()


def test_clear_deletes_previous_value(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
):
    # given
    product_type.product_attributes.add(file_attribute)
    old_value = file_attribute.values.first()
    associate_attribute_values_to_instance(product, {file_attribute.pk: [old_value]})

    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                    "file": None,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    assert (
        AssignedProductAttributeValue.objects.filter(
            product=product, value__attribute=file_attribute
        ).exists()
        is False
    )


def test_same_file_url_keeps_the_value(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
):
    # given
    product_type.product_attributes.add(file_attribute)
    old_value = file_attribute.values.first()
    associate_attribute_values_to_instance(product, {file_attribute.pk: [old_value]})
    values_count = file_attribute.values.count()

    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                    "file": build_file_url(old_value.file_url),
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productUpdate"]["errors"] == []

    assigned_value = AssignedProductAttributeValue.objects.get(
        product=product, value__attribute=file_attribute
    ).value
    assert assigned_value == old_value
    assert file_attribute.values.count() == values_count


def test_failed_mutation_rolls_back_the_delete(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    """A failure after the attribute save must also roll the delete back.

    On productVariantUpdate the product row is saved after the attributes,
    inside the same transaction, so failing that save exercises the rollback
    through the real mutation.
    """
    # given
    variant = product_with_variant_with_file_attribute.variants.first()
    old_value = AssignedVariantAttributeValue.objects.get(
        assignment__variant=variant, value__attribute=file_attribute
    ).value
    values_count = file_attribute.values.count()

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "attributes": [
            {
                "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                "file": build_file_url("new_file.jpg"),
            }
        ],
    }

    # when
    with mock.patch.object(Product, "save", side_effect=RollbackTrigger("injected")):
        response = staff_api_client.post_graphql(
            VARIANT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
        )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1
    assert content["data"]["productVariantUpdate"] is None

    assert AttributeValue.objects.filter(pk=old_value.pk).exists()
    assigned_value = AssignedVariantAttributeValue.objects.get(
        assignment__variant=variant, value__attribute=file_attribute
    ).value
    assert assigned_value == old_value
    assert file_attribute.values.count() == values_count


def test_value_assigned_to_another_entity_is_kept(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    page,
    permission_manage_products,
):
    # given a legacy-shaped value shared between a product and a page
    product_type.product_attributes.add(file_attribute)
    old_value = file_attribute.values.first()
    associate_attribute_values_to_instance(product, {file_attribute.pk: [old_value]})
    page_assignment = AssignedPageAttributeValue.objects.create(
        page=page, value=old_value
    )
    values_count = file_attribute.values.count()

    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                    "file": None,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productUpdate"]["errors"] == []

    assert (
        AssignedProductAttributeValue.objects.filter(
            product=product, value__attribute=file_attribute
        ).exists()
        is False
    )
    assert AttributeValue.objects.filter(pk=old_value.pk).exists()
    assert AssignedPageAttributeValue.objects.filter(pk=page_assignment.pk).exists()
    # clearing must not create any new value either
    assert file_attribute.values.count() == values_count


def test_swatch_values_are_kept(
    staff_api_client,
    product,
    product_type,
    swatch_attribute,
    permission_manage_products,
):
    # given
    product_type.product_attributes.add(swatch_attribute)
    old_choice = swatch_attribute.values.first()
    new_choice = swatch_attribute.values.last()
    associate_attribute_values_to_instance(product, {swatch_attribute.pk: [old_choice]})

    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", swatch_attribute.pk),
                    "swatch": {
                        "id": graphene.Node.to_global_id(
                            "AttributeValue", new_choice.pk
                        )
                    },
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then swatch choices are attribute definition rows and must survive
    content = get_graphql_content(response)
    assert content["data"]["productUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_choice.pk).exists()
    assigned_value = AssignedProductAttributeValue.objects.get(
        product=product, value__attribute=swatch_attribute
    ).value
    assert assigned_value == new_choice


def test_attribute_absent_from_input_is_kept(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
):
    # given a second file attribute that the input does not touch
    other_file_attribute = Attribute.objects.create(
        slug="manual",
        name="Manual",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.FILE,
    )
    other_value = AttributeValue.objects.create(
        attribute=other_file_attribute,
        name="manual.pdf",
        slug="manualpdf",
        file_url="manual.pdf",
    )
    product_type.product_attributes.add(file_attribute, other_file_attribute)
    old_value = file_attribute.values.first()
    associate_attribute_values_to_instance(
        product,
        {file_attribute.pk: [old_value], other_file_attribute.pk: [other_value]},
    )

    file_name = "new_file.jpg"
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                    "file": build_file_url(file_name),
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    new_value = AssignedProductAttributeValue.objects.get(
        product=product, value__attribute=file_attribute
    ).value
    assert new_value.file_url == file_name
    assert AttributeValue.objects.filter(pk=other_value.pk).exists()
    assert AssignedProductAttributeValue.objects.filter(
        product=product, value=other_value
    ).exists()


def test_clear_deletes_all_assigned_values(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
):
    # given a legacy shape with two values assigned for one file attribute
    product_type.product_attributes.add(file_attribute)
    first_value = file_attribute.values.first()
    second_value = file_attribute.values.last()
    associate_attribute_values_to_instance(
        product, {file_attribute.pk: [first_value, second_value]}
    )

    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                    "file": None,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productUpdate"]["errors"] == []

    assert file_attribute.values.exists() is False
    assert (
        AssignedProductAttributeValue.objects.filter(
            product=product, value__attribute=file_attribute
        ).exists()
        is False
    )


def test_variant_replace_deletes_previous_value(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    # given
    variant = product_with_variant_with_file_attribute.variants.first()
    old_value = AssignedVariantAttributeValue.objects.get(
        assignment__variant=variant, value__attribute=file_attribute
    ).value

    file_name = "new_file.jpg"
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "attributes": [
            {
                "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                "file": build_file_url(file_name),
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productVariantUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    new_value = AssignedVariantAttributeValue.objects.get(
        assignment__variant=variant, value__attribute=file_attribute
    ).value
    assert new_value.file_url == file_name


def test_variant_clear_deletes_previous_value(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    # given
    variant = product_with_variant_with_file_attribute.variants.first()
    old_value = AssignedVariantAttributeValue.objects.get(
        assignment__variant=variant, value__attribute=file_attribute
    ).value

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "attributes": [
            {
                "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                "file": None,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productVariantUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    assert (
        AssignedVariantAttributeValue.objects.filter(
            assignment__variant=variant, value__attribute=file_attribute
        ).exists()
        is False
    )


def test_variant_bulk_update_replace_deletes_previous_value(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    # given
    product = product_with_variant_with_file_attribute
    variant = product.variants.first()
    old_value = AssignedVariantAttributeValue.objects.get(
        assignment__variant=variant, value__attribute=file_attribute
    ).value

    file_name = "new_file.jpg"
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "variants": [
            {
                "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
                "attributes": [
                    {
                        "id": graphene.Node.to_global_id(
                            "Attribute", file_attribute.pk
                        ),
                        "file": build_file_url(file_name),
                    }
                ],
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_BULK_UPDATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkUpdate"]
    assert data["count"] == 1
    assert data["results"][0]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    new_value = AssignedVariantAttributeValue.objects.get(
        assignment__variant=variant, value__attribute=file_attribute
    ).value
    assert new_value.file_url == file_name


def test_page_replace_deletes_previous_value(
    staff_api_client,
    page,
    page_file_attribute,
    permission_manage_pages,
):
    # given
    page.page_type.page_attributes.add(page_file_attribute)
    old_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(page, {page_file_attribute.pk: [old_value]})

    file_name = "new_file.jpg"
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "attributes": [
            {
                "id": graphene.Node.to_global_id("Attribute", page_file_attribute.pk),
                "file": build_file_url(file_name),
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PAGE_UPDATE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["pageUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    new_value = AssignedPageAttributeValue.objects.get(
        page=page, value__attribute=page_file_attribute
    ).value
    assert new_value.file_url == file_name


def test_page_clear_deletes_previous_value(
    staff_api_client,
    page,
    page_file_attribute,
    permission_manage_pages,
):
    # given
    page.page_type.page_attributes.add(page_file_attribute)
    old_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(page, {page_file_attribute.pk: [old_value]})

    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "attributes": [
            {
                "id": graphene.Node.to_global_id("Attribute", page_file_attribute.pk),
                "file": None,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PAGE_UPDATE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["pageUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    assert (
        AssignedPageAttributeValue.objects.filter(
            page=page, value__attribute=page_file_attribute
        ).exists()
        is False
    )


def test_customer_update_clear_deletes_previous_value(
    staff_api_client,
    customer_user,
    customer_type,
    permission_manage_users,
):
    # given
    file_attribute = Attribute.objects.create(
        slug="contract",
        name="Contract",
        type=AttributeType.CUSTOMER_TYPE,
        input_type=AttributeInputType.FILE,
    )
    old_value = AttributeValue.objects.create(
        attribute=file_attribute,
        name="contract.pdf",
        slug="contractpdf",
        file_url="contract.pdf",
    )
    customer_type.customer_attributes.add(file_attribute)
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    associate_attribute_values_to_instance(
        customer_user, {file_attribute.pk: [old_value]}
    )

    variables = {
        "id": graphene.Node.to_global_id("User", customer_user.pk),
        "attributes": [
            {
                "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
                "file": None,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_UPDATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerUpdate"]["errors"] == []

    assert AttributeValue.objects.filter(pk=old_value.pk).exists() is False
    assert customer_user.attributevalues.exists() is False
