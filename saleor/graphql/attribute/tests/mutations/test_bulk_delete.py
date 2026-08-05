from unittest import mock

import graphene
import pytest

from .....attribute.models import Attribute, AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import assert_no_permission, get_graphql_content

ATTRIBUTE_BULK_DELETE_MUTATION = """
    mutation attributeBulkDelete($ids: [ID!]!) {
        attributeBulkDelete(ids: $ids) {
            count
        }
    }
"""


@pytest.fixture
def attribute_value_list(color_attribute):
    value_1 = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    value_2 = AttributeValue.objects.create(
        slug="white", name="White", attribute=color_attribute, value="#FFFFFF"
    )
    value_3 = AttributeValue.objects.create(
        slug="black", name="Black", attribute=color_attribute, value="#000000"
    )
    return value_1, value_2, value_3


def test_delete_attributes(
    staff_api_client,
    product_type_attribute_list,
    permission_manage_product_types_and_attributes,
):
    query = ATTRIBUTE_BULK_DELETE_MUTATION

    variables = {
        "ids": [
            graphene.Node.to_global_id("Attribute", attr.id)
            for attr in product_type_attribute_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeBulkDelete"]["count"] == 3
    assert not Attribute.objects.filter(
        id__in=[attr.id for attr in product_type_attribute_list]
    ).exists()


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_attributes_trigger_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product_type_attribute_list,
    permission_manage_product_types_and_attributes,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [
            graphene.Node.to_global_id("Attribute", attr.id)
            for attr in product_type_attribute_list
        ]
    }
    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["attributeBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == 3


def test_delete_attributes_products_search_document_updated(
    staff_api_client,
    product_type_attribute_list,
    permission_manage_product_types_and_attributes,
    product_list,
    color_attribute,
):
    query = ATTRIBUTE_BULK_DELETE_MUTATION
    product_1 = product_list[0]
    product_2 = product_list[1]
    variant_1 = product_1.variants.first()

    product_type = product_1.product_type

    attr_1, attr_2, attr_3 = product_type_attribute_list
    product_type.product_attributes.add(attr_1, attr_2, color_attribute)
    product_type.variant_attributes.add(attr_1, attr_3)

    attr_1_name = "attr 1 value"
    attr_1_value = AttributeValue.objects.create(name=attr_1_name, attribute=attr_1)

    color_attribute_value = color_attribute.values.first()

    attr_2_name = "attr 2 value"
    attr_2_value = AttributeValue.objects.create(name=attr_2_name, attribute=attr_2)

    attr_3_name = "attr 3 value"
    attr_3_value = AttributeValue.objects.create(name=attr_3_name, attribute=attr_3)

    associate_attribute_values_to_instance(
        product_1,
        {attr_1.id: [attr_1_value], color_attribute.id: [color_attribute_value]},
    )
    associate_attribute_values_to_instance(
        product_2,
        {attr_2.id: [attr_2_value]},
    )
    associate_attribute_values_to_instance(
        variant_1,
        {attr_3.id: [attr_3_value]},
    )

    variables = {
        "ids": [
            graphene.Node.to_global_id("Attribute", attr.id)
            for attr in product_type_attribute_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeBulkDelete"]["count"] == 3
    assert not Attribute.objects.filter(
        id__in=[attr.id for attr in product_type_attribute_list]
    ).exists()


ATTRIBUTE_VALUE_BULK_DELETE_MUTATION = """
    mutation attributeValueBulkDelete($ids: [ID!]!) {
        attributeValueBulkDelete(ids: $ids) {
            count
        }
    }
"""


def test_delete_attribute_values(
    staff_api_client,
    attribute_value_list,
    permission_manage_product_types_and_attributes,
):
    query = ATTRIBUTE_VALUE_BULK_DELETE_MUTATION

    variables = {
        "ids": [
            graphene.Node.to_global_id("AttributeValue", val.id)
            for val in attribute_value_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeValueBulkDelete"]["count"] == 3
    assert not AttributeValue.objects.filter(
        id__in=[val.id for val in attribute_value_list]
    ).exists()


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_attribute_values_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    attribute_value_list,
    permission_manage_product_types_and_attributes,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    attributes = {value.attribute for value in attribute_value_list}
    variables = {
        "ids": [
            graphene.Node.to_global_id("AttributeValue", val.id)
            for val in attribute_value_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    expected_call_count = len(attributes) + len(attribute_value_list)

    # then
    assert content["data"]["attributeValueBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == expected_call_count


def test_delete_attribute_values_search_document_updated(
    staff_api_client,
    product_list,
    attribute_value_list,
    permission_manage_product_types_and_attributes,
):
    query = ATTRIBUTE_VALUE_BULK_DELETE_MUTATION
    value_1, value_2, value_3 = attribute_value_list

    attribute = value_1.attribute
    value_4 = AttributeValue.objects.create(
        slug="orange", name="Orange", attribute=attribute, value="#ABCD"
    )

    product_1 = product_list[0]
    product_2 = product_list[1]
    variant_1 = product_1.variants.first()
    product_type = product_1.product_type

    product_type.product_attributes.add(attribute)
    product_type.variant_attributes.add(attribute)

    associate_attribute_values_to_instance(
        product_1,
        {attribute.id: [value_1, value_4]},
    )
    associate_attribute_values_to_instance(
        product_2,
        {attribute.id: [value_2]},
    )
    associate_attribute_values_to_instance(
        variant_1,
        {attribute.id: [value_3]},
    )

    variables = {
        "ids": [
            graphene.Node.to_global_id("AttributeValue", val.id)
            for val in attribute_value_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeValueBulkDelete"]["count"] == 3
    assert not AttributeValue.objects.filter(
        id__in=[val.id for val in attribute_value_list]
    ).exists()

    product_1.refresh_from_db()
    product_2.refresh_from_db()
    assert product_1.search_vector
    assert product_2.search_vector


@pytest.mark.parametrize(
    (
        "_case",
        "client_fixture",
        "attribute_list_fixtures",
        "permission_fixtures",
        "is_allowed",
    ),
    [
        (
            "Unauthenticated user should be rejected",
            "api_client",
            ["product_type_attribute_list"],
            [],
            False,
        ),
        (
            "Unauthenticated user should be rejected even with empty ids",
            "api_client",
            [],
            [],
            False,
        ),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            ["product_type_attribute_list"],
            [],
            False,
        ),
        (
            "Staff user w/o any permission should be rejected",
            "staff_api_client",
            ["product_type_attribute_list"],
            [],
            False,
        ),
        (
            "Product attributes w/ legacy page permission should be allowed",
            "staff_api_client",
            ["product_type_attribute_list"],
            ["permission_manage_page_types_and_attributes"],
            True,
        ),
        (
            "Product attributes w/ product permission should be allowed",
            "staff_api_client",
            ["product_type_attribute_list"],
            ["permission_manage_product_types_and_attributes"],
            True,
        ),
        (
            "Page attributes w/ product permission should be rejected",
            "staff_api_client",
            ["page_type_attribute_list"],
            ["permission_manage_product_types_and_attributes"],
            False,
        ),
        (
            "Page attributes w/ page permission should be allowed",
            "staff_api_client",
            ["page_type_attribute_list"],
            ["permission_manage_page_types_and_attributes"],
            True,
        ),
        (
            "Mixed attributes w/ product permission only should be rejected",
            "staff_api_client",
            ["product_type_attribute_list", "page_type_attribute_list"],
            ["permission_manage_product_types_and_attributes"],
            False,
        ),
        (
            "Mixed attributes w/ legacy page permission only should be allowed",
            "staff_api_client",
            ["product_type_attribute_list", "page_type_attribute_list"],
            ["permission_manage_page_types_and_attributes"],
            True,
        ),
        (
            "Mixed attributes w/ both permissions should be allowed",
            "staff_api_client",
            ["product_type_attribute_list", "page_type_attribute_list"],
            [
                "permission_manage_product_types_and_attributes",
                "permission_manage_page_types_and_attributes",
            ],
            True,
        ),
    ],
)
def test_delete_attributes_authorization(
    request,
    _case,
    client_fixture,
    attribute_list_fixtures,
    permission_fixtures,
    is_allowed,
):
    # given
    client = request.getfixturevalue(client_fixture)
    attributes = [
        attribute
        for fixture in attribute_list_fixtures
        for attribute in request.getfixturevalue(fixture)
    ]
    for permission_fixture in permission_fixtures:
        client.user.user_permissions.add(request.getfixturevalue(permission_fixture))
    attribute_pks = [attribute.pk for attribute in attributes]
    variables = {
        "ids": [graphene.Node.to_global_id("Attribute", pk) for pk in attribute_pks]
    }

    # when
    response = client.post_graphql(ATTRIBUTE_BULK_DELETE_MUTATION, variables)

    # then
    if is_allowed:
        content = get_graphql_content(response)
        assert content["data"]["attributeBulkDelete"]["count"] == len(attributes)
        assert Attribute.objects.filter(pk__in=attribute_pks).exists() is False
    else:
        assert_no_permission(response)
        assert Attribute.objects.filter(pk__in=attribute_pks).count() == len(attributes)


@pytest.mark.parametrize(
    (
        "_case",
        "client_fixture",
        "attribute_fixtures",
        "permission_fixtures",
        "is_allowed",
    ),
    [
        (
            "Unauthenticated user should be rejected",
            "api_client",
            ["color_attribute"],
            [],
            False,
        ),
        (
            "Unauthenticated user should be rejected even with empty ids",
            "api_client",
            [],
            [],
            False,
        ),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            ["color_attribute"],
            [],
            False,
        ),
        (
            "Staff user w/o any permission should be rejected",
            "staff_api_client",
            ["color_attribute"],
            [],
            False,
        ),
        (
            "Product attribute values w/ legacy page permission should be allowed",
            "staff_api_client",
            ["color_attribute"],
            ["permission_manage_page_types_and_attributes"],
            True,
        ),
        (
            "Product attribute values w/ product permission should be allowed",
            "staff_api_client",
            ["color_attribute"],
            ["permission_manage_product_types_and_attributes"],
            True,
        ),
        (
            "Page attribute values w/ product permission should be rejected",
            "staff_api_client",
            ["size_page_attribute"],
            ["permission_manage_product_types_and_attributes"],
            False,
        ),
        (
            "Page attribute values w/ page permission should be allowed",
            "staff_api_client",
            ["size_page_attribute"],
            ["permission_manage_page_types_and_attributes"],
            True,
        ),
        (
            "Mixed attribute values w/ product permission only should be rejected",
            "staff_api_client",
            ["color_attribute", "size_page_attribute"],
            ["permission_manage_product_types_and_attributes"],
            False,
        ),
        (
            "Mixed attribute values w/ legacy page permission only should be allowed",
            "staff_api_client",
            ["color_attribute", "size_page_attribute"],
            ["permission_manage_page_types_and_attributes"],
            True,
        ),
        (
            "Mixed attribute values w/ both permissions should be allowed",
            "staff_api_client",
            ["color_attribute", "size_page_attribute"],
            [
                "permission_manage_product_types_and_attributes",
                "permission_manage_page_types_and_attributes",
            ],
            True,
        ),
    ],
)
def test_delete_attribute_values_authorization(
    request,
    _case,
    client_fixture,
    attribute_fixtures,
    permission_fixtures,
    is_allowed,
):
    # given
    client = request.getfixturevalue(client_fixture)
    value_pks = [
        pk
        for fixture in attribute_fixtures
        for pk in request.getfixturevalue(fixture).values.values_list("pk", flat=True)
    ]
    for permission_fixture in permission_fixtures:
        client.user.user_permissions.add(request.getfixturevalue(permission_fixture))
    variables = {
        "ids": [graphene.Node.to_global_id("AttributeValue", pk) for pk in value_pks]
    }

    # when
    response = client.post_graphql(ATTRIBUTE_VALUE_BULK_DELETE_MUTATION, variables)

    # then
    if is_allowed:
        content = get_graphql_content(response)
        assert content["data"]["attributeValueBulkDelete"]["count"] == len(value_pks)
        assert AttributeValue.objects.filter(pk__in=value_pks).exists() is False
    else:
        assert_no_permission(response)
        assert AttributeValue.objects.filter(pk__in=value_pks).count() == len(value_pks)
