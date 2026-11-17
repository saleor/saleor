import graphene
import pytest

from .....core.error_codes import MetadataErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import EXTERNAL_REFERENCE_TYPE_TO_MODEL, ExternalReferenceTypeEnum
from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

EXTERNAL_REFERENCE = "external-reference-1"

UPDATE_METADATA_MUTATION = """
mutation UpdateMetadata(
    $id: ID
    $externalReference: String
    $type: ExternalReferenceTypeEnum
    $input: [MetadataInput!]!
) {
    updateMetadata(
        id: $id
        externalReference: $externalReference
        type: $type
        input: $input
    ) {
        errors {
            field
            code
            message
        }
        item {
            ... on Node {
                id
            }
        }
    }
}
"""

UPDATE_PRIVATE_METADATA_MUTATION = """
mutation UpdatePrivateMetadata(
    $id: ID
    $externalReference: String
    $type: ExternalReferenceTypeEnum
    $input: [MetadataInput!]!
) {
    updatePrivateMetadata(
        id: $id
        externalReference: $externalReference
        type: $type
        input: $input
    ) {
        errors {
            field
            code
            message
        }
        item {
            ... on Node {
                id
            }
        }
    }
}
"""

DELETE_METADATA_MUTATION = """
mutation DeleteMetadata(
    $id: ID
    $externalReference: String
    $type: ExternalReferenceTypeEnum
    $keys: [String!]!
) {
    deleteMetadata(
        id: $id
        externalReference: $externalReference
        type: $type
        keys: $keys
    ) {
        errors {
            field
            code
            message
        }
        item {
            ... on Node {
                id
            }
        }
    }
}
"""

DELETE_PRIVATE_METADATA_MUTATION = """
mutation DeletePrivateMetadata(
    $id: ID
    $externalReference: String
    $type: ExternalReferenceTypeEnum
    $keys: [String!]!
) {
    deletePrivateMetadata(
        id: $id
        externalReference: $externalReference
        type: $type
        keys: $keys
    ) {
        errors {
            field
            code
            message
        }
        item {
            ... on Node {
                id
            }
        }
    }
}
"""


def test_external_reference_type_enum_covers_mapped_models():
    # given
    enum_values = {member.value for member in ExternalReferenceTypeEnum._meta.enum}

    # when
    mapped_types = set(EXTERNAL_REFERENCE_TYPE_TO_MODEL)

    # then
    assert enum_values == mapped_types


@pytest.mark.parametrize(
    ("_case", "object_fixture", "reference_type", "permission_fixture"),
    [
        (
            "attribute",
            "color_attribute",
            ExternalReferenceTypeEnum.ATTRIBUTE,
            "permission_manage_product_types_and_attributes",
        ),
        (
            "category",
            "category",
            ExternalReferenceTypeEnum.CATEGORY,
            "permission_manage_products",
        ),
        (
            "collection",
            "collection",
            ExternalReferenceTypeEnum.COLLECTION,
            "permission_manage_products",
        ),
        ("order", "order", ExternalReferenceTypeEnum.ORDER, "permission_manage_orders"),
        (
            "product",
            "product",
            ExternalReferenceTypeEnum.PRODUCT,
            "permission_manage_products",
        ),
        (
            "product_variant",
            "variant",
            ExternalReferenceTypeEnum.PRODUCT_VARIANT,
            "permission_manage_products",
        ),
        (
            "promotion",
            "catalogue_promotion",
            ExternalReferenceTypeEnum.PROMOTION,
            "permission_manage_discounts",
        ),
        (
            "voucher",
            "voucher",
            ExternalReferenceTypeEnum.VOUCHER,
            "permission_manage_discounts",
        ),
        (
            "warehouse",
            "warehouse",
            ExternalReferenceTypeEnum.WAREHOUSE,
            "permission_manage_products",
        ),
    ],
)
def test_update_metadata_by_external_reference(
    _case,
    object_fixture,
    reference_type,
    permission_fixture,
    request,
    staff_api_client,
):
    # given
    instance = request.getfixturevalue(object_fixture)
    instance.external_reference = EXTERNAL_REFERENCE
    instance.save(update_fields=["external_reference"])
    expected_metadata = {**instance.metadata, PUBLIC_KEY: PUBLIC_VALUE}
    permission = request.getfixturevalue(permission_fixture)
    staff_api_client.user.user_permissions.add(permission)

    variables = {
        "externalReference": EXTERNAL_REFERENCE,
        "type": reference_type.name,
        "input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}],
    }

    # when
    response = staff_api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["updateMetadata"]
    assert data["errors"] == []
    assert data["item"]["id"] == graphene.Node.to_global_id(
        reference_type.value, instance.pk
    )
    instance.refresh_from_db(fields=["metadata"])
    assert instance.metadata == expected_metadata


@pytest.mark.parametrize(
    (
        "_case",
        "mutation",
        "mutation_name",
        "initial_metadata",
        "initial_private_metadata",
        "arguments",
        "expected_metadata",
        "expected_private_metadata",
    ),
    [
        (
            "update_metadata",
            UPDATE_METADATA_MUTATION,
            "updateMetadata",
            {},
            {},
            {"input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}]},
            {PUBLIC_KEY: PUBLIC_VALUE},
            {},
        ),
        (
            "update_private_metadata",
            UPDATE_PRIVATE_METADATA_MUTATION,
            "updatePrivateMetadata",
            {},
            {},
            {"input": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}]},
            {},
            {PRIVATE_KEY: PRIVATE_VALUE},
        ),
        (
            "delete_metadata",
            DELETE_METADATA_MUTATION,
            "deleteMetadata",
            {PUBLIC_KEY: PUBLIC_VALUE},
            {PRIVATE_KEY: PRIVATE_VALUE},
            {"keys": [PUBLIC_KEY]},
            {},
            {PRIVATE_KEY: PRIVATE_VALUE},
        ),
        (
            "delete_private_metadata",
            DELETE_PRIVATE_METADATA_MUTATION,
            "deletePrivateMetadata",
            {PUBLIC_KEY: PUBLIC_VALUE},
            {PRIVATE_KEY: PRIVATE_VALUE},
            {"keys": [PRIVATE_KEY]},
            {PUBLIC_KEY: PUBLIC_VALUE},
            {},
        ),
    ],
)
def test_metadata_mutations_by_external_reference(
    _case,
    mutation,
    mutation_name,
    initial_metadata,
    initial_private_metadata,
    arguments,
    expected_metadata,
    expected_private_metadata,
    staff_api_client,
    permission_manage_products,
    product,
):
    # given
    product.external_reference = EXTERNAL_REFERENCE
    product.metadata = initial_metadata
    product.private_metadata = initial_private_metadata
    product.save(update_fields=["external_reference", "metadata", "private_metadata"])
    staff_api_client.user.user_permissions.add(permission_manage_products)

    variables = {
        "externalReference": EXTERNAL_REFERENCE,
        "type": ExternalReferenceTypeEnum.PRODUCT.name,
        **arguments,
    }

    # when
    response = staff_api_client.post_graphql(mutation, variables)

    # then
    data = get_graphql_content(response)["data"][mutation_name]
    assert data["errors"] == []
    assert data["item"]["id"] == graphene.Node.to_global_id("Product", product.pk)
    product.refresh_from_db(fields=["metadata", "private_metadata"])
    assert product.metadata == expected_metadata
    assert product.private_metadata == expected_private_metadata


@pytest.mark.parametrize(
    ("_case", "arguments", "expected_field", "expected_code", "expected_message"),
    [
        (
            "id_and_external_reference",
            {
                "id": "product-id",
                "externalReference": EXTERNAL_REFERENCE,
                "type": ExternalReferenceTypeEnum.PRODUCT.name,
            },
            None,
            MetadataErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'externalReference'",
        ),
        (
            "no_identifier",
            {},
            None,
            MetadataErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "null_identifiers",
            {"id": None, "externalReference": None},
            None,
            MetadataErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "external_reference_without_type",
            {"externalReference": EXTERNAL_REFERENCE},
            "type",
            MetadataErrorCode.REQUIRED,
            "Argument 'type' is required when 'externalReference' is provided.",
        ),
        (
            "external_reference_with_null_type",
            {"externalReference": EXTERNAL_REFERENCE, "type": None},
            "type",
            MetadataErrorCode.REQUIRED,
            "Argument 'type' is required when 'externalReference' is provided.",
        ),
        (
            "type_without_external_reference",
            {
                "id": "product-id",
                "type": ExternalReferenceTypeEnum.PRODUCT.name,
            },
            "type",
            MetadataErrorCode.INVALID,
            "Argument 'type' can only be used with 'externalReference'.",
        ),
        (
            "non_existing_external_reference",
            {
                "externalReference": "non-existing",
                "type": ExternalReferenceTypeEnum.PRODUCT.name,
            },
            "externalReference",
            MetadataErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: non-existing",
        ),
        (
            "external_reference_of_other_type",
            {
                "externalReference": EXTERNAL_REFERENCE,
                "type": ExternalReferenceTypeEnum.CATEGORY.name,
            },
            "externalReference",
            MetadataErrorCode.NOT_FOUND,
            f"Couldn't resolve to a node: {EXTERNAL_REFERENCE}",
        ),
    ],
)
def test_update_metadata_by_external_reference_invalid_arguments(
    _case,
    arguments,
    expected_field,
    expected_code,
    expected_message,
    staff_api_client,
    permission_manage_products,
    product,
):
    # given
    product.external_reference = EXTERNAL_REFERENCE
    product.metadata = {}
    product.save(update_fields=["external_reference", "metadata"])
    staff_api_client.user.user_permissions.add(permission_manage_products)

    variables = {"input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}], **arguments}

    # when
    response = staff_api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["updateMetadata"]
    assert data["item"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == expected_field
    assert error["code"] == expected_code.name
    assert error["message"] == expected_message
    product.refresh_from_db(fields=["metadata"])
    assert product.metadata == {}


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", None, False),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/o the permission should be rejected",
            "staff_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/ the correct permission should be allowed",
            "staff_api_client",
            "permission_manage_products",
            True,
        ),
    ],
)
def test_update_metadata_by_external_reference_authorization(
    _case, client_fixture, permission_fixture, is_allowed, request, product
):
    # given
    product.external_reference = EXTERNAL_REFERENCE
    product.metadata = {}
    product.save(update_fields=["external_reference", "metadata"])
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        permission = request.getfixturevalue(permission_fixture)
        client.user.user_permissions.add(permission)

    variables = {
        "externalReference": EXTERNAL_REFERENCE,
        "type": ExternalReferenceTypeEnum.PRODUCT.name,
        "input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}],
    }

    # when
    response = client.post_graphql(UPDATE_METADATA_MUTATION, variables)

    # then
    product.refresh_from_db(fields=["metadata"])
    if is_allowed:
        data = get_graphql_content(response)["data"]["updateMetadata"]
        assert data["errors"] == []
        assert data["item"]["id"] == graphene.Node.to_global_id("Product", product.pk)
        assert product.metadata == {PUBLIC_KEY: PUBLIC_VALUE}
    else:
        assert_no_permission(response)
        assert product.metadata == {}


def test_update_metadata_by_non_existing_external_reference_without_permission(
    staff_api_client,
):
    # given
    variables = {
        "externalReference": "non-existing",
        "type": ExternalReferenceTypeEnum.PRODUCT.name,
        "input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}],
    }

    # when
    response = staff_api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    ("_case", "attribute_fixture", "is_allowed"),
    [
        ("page type attribute is allowed", "size_page_attribute", True),
        ("product type attribute is rejected", "color_attribute", False),
    ],
)
def test_update_attribute_metadata_by_external_reference_checks_attribute_type(
    _case,
    attribute_fixture,
    is_allowed,
    request,
    staff_api_client,
    permission_manage_page_types_and_attributes,
):
    # given
    attribute = request.getfixturevalue(attribute_fixture)
    attribute.external_reference = EXTERNAL_REFERENCE
    attribute.metadata = {}
    attribute.save(update_fields=["external_reference", "metadata"])
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )

    variables = {
        "externalReference": EXTERNAL_REFERENCE,
        "type": ExternalReferenceTypeEnum.ATTRIBUTE.name,
        "input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}],
    }

    # when
    response = staff_api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)

    # then
    attribute.refresh_from_db(fields=["metadata"])
    if is_allowed:
        data = get_graphql_content(response)["data"]["updateMetadata"]
        assert data["errors"] == []
        assert data["item"]["id"] == graphene.Node.to_global_id(
            "Attribute", attribute.pk
        )
        assert attribute.metadata == {PUBLIC_KEY: PUBLIC_VALUE}
    else:
        assert_no_permission(response)
        assert attribute.metadata == {}
