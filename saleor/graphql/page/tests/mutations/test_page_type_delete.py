from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....attribute.utils import associate_attribute_values_to_instance
from .....page.models import Page
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import assert_no_permission, get_graphql_content

DELETE_PAGE_TYPE_MUTATION = """
    mutation DeletePageType($id: ID!) {
        pageTypeDelete(id: $id) {
            pageType {
                id
                name
                slug
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_page_type_delete_by_staff(
    staff_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )

    pages_pks = list(page_type.pages.values_list("pk", flat=True))

    assert pages_pks

    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = staff_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeDelete"]

    assert not data["errors"]
    assert data["pageType"]["id"] == page_type_id

    with pytest.raises(page_type._meta.model.DoesNotExist):
        page_type.refresh_from_db()

    # ensure that corresponding pages has been removed
    assert not Page.objects.filter(pk__in=pages_pks)


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_type_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page_type,
    page,
    permission_manage_page_types_and_attributes,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # when
    response = staff_api_client.post_graphql(
        DELETE_PAGE_TYPE_MUTATION, {"id": page_type_id}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeDelete"]

    assert not data["errors"]
    assert data["pageType"]["id"] == page_type_id
    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": page_type_id,
            "name": page_type.name,
            "slug": page_type.slug,
            "meta": generate_meta(
                requestor_data=generate_requestor(
                    SimpleLazyObject(lambda: staff_api_client.user)
                )
            ),
        },
        WebhookEventAsyncType.PAGE_TYPE_DELETED,
        [any_webhook],
        page_type,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_page_type_delete_by_staff_no_perm(
    staff_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = staff_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_page_type_delete_by_app(
    app_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    app_api_client.app.permissions.add(permission_manage_page_types_and_attributes)

    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    pages_pks = list(page_type.pages.values_list("pk", flat=True))

    assert pages_pks

    variables = {"id": page_type_id}

    # when
    response = app_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeDelete"]

    assert not data["errors"]
    assert data["pageType"]["id"] == page_type_id

    with pytest.raises(page_type._meta.model.DoesNotExist):
        page_type.refresh_from_db()

    # ensure that corresponding pages has been removed
    assert not Page.objects.filter(pk__in=pages_pks)


def test_page_type_delete_by_app_no_perm(
    app_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = app_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_page_type_delete_with_file_attributes(
    staff_api_client,
    page_type,
    page,
    page_file_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )
    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)

    value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(page, page_file_attribute, value)
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = staff_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeDelete"]

    assert not data["errors"]
    assert data["pageType"]["id"] == page_type_id

    with pytest.raises(page_type._meta.model.DoesNotExist):
        page_type.refresh_from_db()
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()
