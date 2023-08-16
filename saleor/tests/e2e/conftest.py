import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.test.client import MULTIPART_CONTENT, Client

from ...account.models import User
from ...app.models import App
from ...graphql.tests.fixtures import BaseApiClient
from ..utils import flush_post_commit_hooks
from .channel.utils import create_channel
from .product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from .shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from .utils import assign_permissions
from .warehouse.utils import create_warehouse


class E2eApiClient(BaseApiClient):
    def post_graphql(
        self,
        query,
        variables=None,
        **kwargs,
    ):
        """Dedicated helper for posting GraphQL queries.

        Sets the `application/json` content type and json.dumps the variables
        if present.
        """
        data = {"query": query}
        if variables is not None:
            data["variables"] = variables
        data = json.dumps(data, cls=DjangoJSONEncoder)
        kwargs["content_type"] = "application/json"

        result = super(Client, self).post(self.api_path, data, **kwargs)
        flush_post_commit_hooks()
        return result

    def post_multipart(self, *args, **kwargs):
        """Send a multipart POST request.

        This is used to send multipart requests to GraphQL API when e.g.
        uploading files.
        """
        kwargs["content_type"] = MULTIPART_CONTENT

        result = super(Client, self).post(self.api_path, *args, **kwargs)
        flush_post_commit_hooks()
        return result


@pytest.fixture
def e2e_staff_api_client(
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
):
    e2e_staff_user = User.objects.create_user(
        email="e2e_staff_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )

    client = E2eApiClient(user=e2e_staff_user)

    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
    ]
    assign_permissions(client, permissions)

    return client


@pytest.fixture
def e2e_logged_api_client():
    e2e_customer = User.objects.create_user(
        email="JoeCustomer@example.com",
        password="password",
        first_name="Joe",
        last_name="Saleor",
        is_active=True,
        is_staff=False,
    )
    return E2eApiClient(user=e2e_customer)


@pytest.fixture
def e2e_not_logged_api_client():
    return E2eApiClient()


def e2e_app_api_client():
    e2e_app = App.objects.create(
        name="e2e app",
        is_active=True,
        identifier="saleor.e2e.app.test",
    )
    return E2eApiClient(app=e2e_app)


@pytest.fixture
def prepare_product(e2e_staff_api_client):
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    channel_slug = "test"
    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        e2e_staff_api_client, slug=channel_slug, warehouse_ids=warehouse_ids
    )
    channel_id = channel_data["id"]

    channel_ids = [channel_id]
    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=warehouse_ids,
        channel_ids=channel_ids,
    )
    shipping_zone_id = shipping_zone_data["id"]

    shipping_method_data = create_shipping_method(
        e2e_staff_api_client, shipping_zone_id
    )
    shipping_method_id = shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client, shipping_method_id, channel_id
    )

    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(e2e_staff_api_client, product_type_id, category_id)
    product_id = product_data["id"]

    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    product_variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    product_variant_id = product_variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
    )
    return product_variant_id, channel_id
