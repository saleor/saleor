from ...graphql.tests.utils import get_graphql_content  # noqa: F401
from ...graphql.tests.utils import get_multipart_request_body  # noqa: F401


def assign_permissions(api_client, permissions):
    user = api_client.user
    if user:
        user.user_permissions.add(*permissions)
