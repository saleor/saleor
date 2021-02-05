import graphene

from ....core.error_codes import ShopErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content

CATEGORY_SETTINGS_UPDATE_MUTATION = """
    mutation CategoryAttributeSettingsUpdate($input: CategoryAttributeSettingsInput!) {
        categoryAttributeSettingsUpdate(input: $input) {
            categoryAttributeSettings {
                attributes {
                    id
                }
            }
            shopErrors {
                code
                field
                attributes
            }
        }
    }
"""


def test_category_settings_update_by_staff(
    staff_api_client,
    site_settings_with_category_attributes,
    page_type_page_reference_attribute,
    tag_page_attribute,
    size_page_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [page_type_page_reference_attribute, tag_page_attribute]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [size_page_attribute]
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryAttributeSettingsUpdate"]
    attr_data = data["categoryAttributeSettings"]["attributes"]
    errors = data["shopErrors"]

    assert not errors
    assert len(attr_data) == len(add_attrs)
    assert {attr["id"] for attr in attr_data} == set(add_attrs)

    site_settings.refresh_from_db()
    assert size_page_attribute.pk not in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )


def test_category_settings_update_by_staff_only_remove_attrs(
    staff_api_client,
    site_settings_with_category_attributes,
    size_page_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    variables = {
        "input": {
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [size_page_attribute]
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryAttributeSettingsUpdate"]
    attr_data = data["categoryAttributeSettings"]["attributes"]
    errors = data["shopErrors"]

    assert not errors
    assert len(attr_data) == 0

    site_settings.refresh_from_db()
    assert size_page_attribute.pk not in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )


def test_category_settings_update_add_existing_attr(
    staff_api_client,
    site_settings_with_category_attributes,
    page_type_page_reference_attribute,
    size_page_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [
            page_type_page_reference_attribute,
            size_page_attribute,
        ]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryAttributeSettingsUpdate"]
    attr_data = data["categoryAttributeSettings"]["attributes"]
    errors = data["shopErrors"]

    assert not errors
    assert len(attr_data) == len(add_attrs)
    assert {attr["id"] for attr in attr_data} == set(add_attrs)


def test_category_settings_update_by_staff_no_perm(
    staff_api_client,
    site_settings_with_category_attributes,
    page_type_page_reference_attribute,
    tag_page_attribute,
    size_page_attribute,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [page_type_page_reference_attribute, tag_page_attribute]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [size_page_attribute]
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_category_settings_update_by_app(
    app_api_client,
    site_settings_with_category_attributes,
    page_type_page_reference_attribute,
    size_page_attribute,
    tag_page_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes
    app_api_client.app.permissions.add(permission_manage_page_types_and_attributes)

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [page_type_page_reference_attribute, tag_page_attribute]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
        }
    }

    # when
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryAttributeSettingsUpdate"]
    attr_data = data["categoryAttributeSettings"]["attributes"]
    errors = data["shopErrors"]

    assert not errors
    assert len(attr_data) == len(add_attrs) + 1
    add_attrs = set(add_attrs)
    add_attrs.add(graphene.Node.to_global_id("Attribute", size_page_attribute.pk))
    assert {attr["id"] for attr in attr_data} == add_attrs


def test_category_settings_update_by_customer(
    user_api_client,
    site_settings_with_category_attributes,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
    size_page_attribute,
    tag_page_attribute,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [page_type_page_reference_attribute, tag_page_attribute]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [page_type_product_reference_attribute]
            ],
        }
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_category_settings_update_duplicated_attrs(
    staff_api_client,
    site_settings_with_category_attributes,
    page_type_product_reference_attribute,
    size_page_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [page_type_product_reference_attribute, size_page_attribute]
    ]
    remove_attributes = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [size_page_attribute]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
            "removeAttributes": remove_attributes,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryAttributeSettingsUpdate"]
    attr_data = data["categoryAttributeSettings"]
    errors = data["shopErrors"]

    assert not attr_data
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == ShopErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["attributes"] == remove_attributes


def test_category_settings_update_assign_product_attribute(
    staff_api_client,
    site_settings_with_category_attributes,
    page_type_product_reference_attribute,
    size_page_attribute,
    weight_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_UPDATE_MUTATION
    site_settings = site_settings_with_category_attributes

    assert size_page_attribute.pk in site_settings.category_attributes.values_list(
        "attribute_id", flat=True
    )

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [page_type_product_reference_attribute, weight_attribute]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryAttributeSettingsUpdate"]
    attr_data = data["categoryAttributeSettings"]
    errors = data["shopErrors"]

    assert not attr_data
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == ShopErrorCode.INVALID.name
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", weight_attribute.pk)
    ]
