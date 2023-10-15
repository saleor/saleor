from typing import List

import graphene
from django.http import HttpResponse

from .....core.models import ModelWithMetadata
from .....permission.models import Permission
from ....tests.fixtures import ApiClient
from ....tests.utils import get_graphql_content

PRIVATE_KEY = "private_key"
PRIVATE_VALUE = "private_vale"

PUBLIC_KEY = "key"
PUBLIC_KEY2 = "key2"
PUBLIC_VALUE = "value"
PUBLIC_VALUE2 = "value2"


def execute_query(
    query_str: str,
    client: ApiClient,
    model: ModelWithMetadata,
    model_name: str,
    permissions: List[Permission] = None,
):
    return client.post_graphql(
        query_str,
        variables={"id": graphene.Node.to_global_id(model_name, model.pk)},
        permissions=[] if permissions is None else permissions,
        check_no_permissions=False,
    )


def assert_model_contains_private_metadata(response: HttpResponse, model_name: str):
    content = get_graphql_content(response)
    metadata = content["data"][model_name]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def assert_model_contains_metadata(response: HttpResponse, model_name: str):
    content = get_graphql_content(response)
    metadata = content["data"][model_name]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
