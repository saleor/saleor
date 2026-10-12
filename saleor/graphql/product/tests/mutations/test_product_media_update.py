from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....product.error_codes import ProductErrorCode

PRODUCT_MEDIA_UPDATE_QUERY = """
    mutation updateProductMedia($mediaId: ID!, $alt: String) {
        productMediaUpdate(id: $mediaId, input: {alt: $alt}) {
            media {
                alt
            }
            errors {
                code
                field
            }
        }
    }
    """


@patch("saleor.plugins.manager.PluginsManager.product_media_updated")
@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_image_update_mutation(
    product_updated_mock,
    product_media_update_mock,
    monkeypatch,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given

    media_obj = product_with_image.media.first()
    alt = "damage alt"
    assert media_obj.alt != alt
    variables = {
        "alt": alt,
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_QUERY, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    media_obj.refresh_from_db()
    assert content["data"]["productMediaUpdate"]["media"]["alt"] == alt
    assert media_obj.alt == alt

    product_updated_mock.assert_called_once_with(product_with_image)
    product_media_update_mock.assert_called_once_with(media_obj)


def test_product_image_update_mutation_alt_over_char_limit(
    monkeypatch,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given
    media_obj = product_with_image.media.first()
    alt_over_250 = """
    Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
    Aenean commodo ligula eget dolor. Aenean massa. Cym sociis natoque penatibus et
    magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies
    nec, pellentesque eu, pretium quis, sem.
    """
    variables = {
        "alt": alt_over_250,
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_QUERY, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name


PRODUCT_MEDIA_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation updateProductMedia(
        $id: ID, $externalReference: String, $input: ProductMediaUpdateInput!
    ) {
        productMediaUpdate(
            id: $id, externalReference: $externalReference, input: $input
        ) {
            media {
                alt
                externalReference
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_update_by_external_reference(
    staff_api_client, product_with_image, permission_manage_products, mocker
):
    # given
    media = product_with_image.media.get()
    external_reference = "test-ext-ref"
    media.external_reference = external_reference
    media.save(update_fields=["external_reference"])
    product_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_updated"
    )
    media_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_media_updated"
    )
    alt = "New alt"
    variables = {"externalReference": external_reference, "input": {"alt": alt}}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productMediaUpdate"]
    assert data["errors"] == []
    assert data["media"] == {"alt": alt, "externalReference": external_reference}
    media.refresh_from_db(fields=("alt", "external_reference"))
    assert media.alt == alt
    assert media.external_reference == external_reference
    product_updated_mock.assert_called_once_with(product_with_image)
    media_updated_mock.assert_called_once_with(media)


@pytest.mark.parametrize(
    ("_case", "external_reference"),
    [
        ("non_empty", "test-ext-ref"),
        ("empty_string", ""),
    ],
)
def test_with_non_unique_external_reference(
    _case,
    external_reference,
    staff_api_client,
    product_with_image_list,
    permission_manage_products,
    mocker,
):
    # given
    media, other_media = product_with_image_list.media.all()
    other_media.external_reference = external_reference
    other_media.save(update_fields=["external_reference"])
    original_alt = media.alt
    product_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_updated"
    )
    media_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_media_updated"
    )
    variables = {
        "id": graphene.Node.to_global_id("ProductMedia", media.pk),
        "input": {"alt": "Changed alt", "externalReference": external_reference},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productMediaUpdate"]
    assert data["media"] is None
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["message"]
        == "Product media with this External reference already exists."
    )
    assert errors[0]["field"] == "externalReference"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name
    media.refresh_from_db(fields=("alt", "external_reference"))
    assert media.alt == original_alt
    assert media.external_reference is None
    product_updated_mock.assert_not_called()
    media_updated_mock.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'external_reference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            ProductErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    product_with_image,
    permission_manage_products,
    mocker,
):
    # given
    media = product_with_image.media.get()
    media.external_reference = "existing-reference"
    media.save(update_fields=("external_reference",))
    original_alt = media.alt
    original_reference = media.external_reference
    product_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_updated"
    )
    media_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_media_updated"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("ProductMedia", media.pk)
    variables["input"] = {"alt": "Changed alt"}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["productMediaUpdate"]
    assert data["media"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    media.refresh_from_db(fields=("alt", "external_reference"))
    assert media.alt == original_alt
    assert media.external_reference == original_reference
    product_updated_mock.assert_not_called()
    media_updated_mock.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    product_with_image,
    permission_manage_products,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    media = product_with_image.media.get()
    media.external_reference = "existing-reference"
    media.save(update_fields=("external_reference",))
    original_alt = media.alt
    original_reference = media.external_reference
    alt = "Changed alt"
    product_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_updated"
    )
    media_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_media_updated"
    )
    variables = {"externalReference": original_reference, "input": {"alt": alt}}

    # when
    response = client.post_graphql(
        PRODUCT_MEDIA_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["productMediaUpdate"]
        assert data["errors"] == []
        media.refresh_from_db(fields=("alt", "external_reference"))
        assert media.alt == alt
        assert media.external_reference == original_reference
        assert data["media"] == {"alt": alt, "externalReference": original_reference}
        product_updated_mock.assert_called_once_with(product_with_image)
        media_updated_mock.assert_called_once_with(media)
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"productMediaUpdate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["productMediaUpdate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        media.refresh_from_db(fields=("alt", "external_reference"))
        assert media.alt == original_alt
        assert media.external_reference == original_reference
        product_updated_mock.assert_not_called()
        media_updated_mock.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "reference_input", "expected_reference"),
    [
        ("changed", {"externalReference": "new-reference"}, "new-reference"),
        ("cleared", {"externalReference": None}, None),
        ("omitted", {}, "original-reference"),
    ],
)
def test_external_reference_input(
    _case,
    reference_input,
    expected_reference,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given
    media = product_with_image.media.get()
    media.external_reference = "original-reference"
    media.save(update_fields=("external_reference",))
    alt = "Updated alt"
    variables = {
        "externalReference": media.external_reference,
        "input": {"alt": alt, **reference_input},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    data = get_graphql_content(response)["data"]["productMediaUpdate"]
    assert data["errors"] == []
    assert data["media"] == {"alt": alt, "externalReference": expected_reference}
    media.refresh_from_db(fields=("alt", "external_reference"))
    assert media.alt == alt
    assert media.external_reference == expected_reference
