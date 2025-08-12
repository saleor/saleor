from functools import partial
from unittest import mock
from unittest.mock import ANY

import graphene
import pytest
from django.utils.functional import SimpleLazyObject

from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....product.search import update_products_search_vector
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import get_graphql_content

PAGE_DELETE_MUTATION = """
    mutation DeletePage($id: ID!) {
        pageDelete(id: $id) {
            page {
                title
                id
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_page_delete_mutation(staff_api_client, page, permission_manage_pages):
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page,
    permission_manage_pages,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PAGE_DELETED,
        [any_webhook],
        page,
        SimpleLazyObject(lambda: staff_api_client.user),
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_delete_trigger_webhook_with_page_type(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page,
    permission_manage_pages,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()

    mocked_webhook_trigger.assert_called_once()
    sent_page = mocked_webhook_trigger.call_args.args[3]

    assert sent_page.page_type is not None


def test_page_delete_with_file_attribute(
    staff_api_client,
    page,
    permission_manage_pages,
    page_file_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    existing_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(
        page, {page_file_attribute.pk: [existing_value]}
    )

    variables = {"id": graphene.Node.to_global_id("Page", page.id)}

    # when
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()
    with pytest.raises(existing_value._meta.model.DoesNotExist):
        existing_value.refresh_from_db()


def test_page_delete_removes_reference_to_product(
    product_type_page_reference_attribute,
    page,
    product_type,
    product,
    staff_api_client,
    permission_manage_pages,
):
    query = PAGE_DELETE_MUTATION

    product_type.product_attributes.add(product_type_page_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{product.pk}_{page.pk}",
        reference_page=page,
    )

    associate_attribute_values_to_instance(
        product, {product_type_page_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Page", page.pk)

    variables = {"id": reference_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()

    assert not data["errors"]


def test_page_delete_removes_reference_to_product_variant(
    product_type_page_reference_attribute,
    staff_api_client,
    page,
    variant,
    permission_manage_pages,
):
    query = PAGE_DELETE_MUTATION

    product_type = variant.product.product_type
    product_type.variant_attributes.set([product_type_page_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{variant.pk}_{page.pk}",
        reference_page=page,
    )

    associate_attribute_values_to_instance(
        variant, {product_type_page_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Page", page.pk)

    variables = {"id": reference_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()

    assert not data["errors"]


def test_page_delete_removes_reference_to_page(
    page_type_page_reference_attribute,
    staff_api_client,
    page_list,
    page_type,
    permission_manage_pages,
):
    page = page_list[0]
    page_ref = page_list[1]

    query = PAGE_DELETE_MUTATION

    page_type.page_attributes.add(page_type_page_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{page_ref.pk}",
        reference_page=page_ref,
    )

    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Page", page_ref.pk)

    variables = {"id": reference_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(page_ref._meta.model.DoesNotExist):
        page_ref.refresh_from_db()

    assert not data["errors"]


def test_page_delete_reference_attribute_sets_search_index_dirty_in_product(
    product_type_page_reference_attribute,
    page,
    product,
    staff_api_client,
    permission_manage_pages,
):
    # given
    query = PAGE_DELETE_MUTATION

    # Set up page reference attribute
    attribute = product_type_page_reference_attribute
    product.product_type.product_attributes.add(attribute)
    page.title = "Brand"
    page.save(update_fields=["title"])

    attr_value = AttributeValue.objects.create(
        attribute=attribute,
        name=page.title,
        slug=f"{product.pk}_{page.pk}",
        reference_page=page,
    )

    associate_attribute_values_to_instance(product, {attribute.pk: [attr_value]})

    # Ensure product search index is initially clean
    product.search_index_dirty = False
    product.save(update_fields=["search_index_dirty"])
    update_products_search_vector([product.id])
    product.refresh_from_db()
    assert page.title.lower() in product.search_vector

    # when
    page_id = graphene.Node.to_global_id("Page", page.pk)
    variables = {"id": page_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]

    # Check that page was deleted
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()

    # Check that attribute value was deleted
    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()

    # Check that product search_index_dirty flag was set to True
    product.refresh_from_db(fields=["search_index_dirty"])
    assert product.search_index_dirty is True
    assert not data["errors"]

    update_products_search_vector([product.id])
    product.refresh_from_db()
    assert page.title.lower() not in product.search_vector
