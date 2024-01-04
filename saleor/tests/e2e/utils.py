import json

from ...account.models import Group
from ...graphql.tests.utils import (
    get_graphql_content,  # noqa: F401
    get_multipart_request_body,  # noqa: F401
)


def assign_permissions(api_client, permissions):
    user = api_client.user
    if user:
        group = Group.objects.create(
            name="admins",
            restricted_access_to_channels=False,
        )
        group.permissions.add(*permissions)
        user.groups.add(group)
    else:
        app = api_client.app
        if app:
            app.permissions.add(*permissions)


def request_matcher(r1, r2):
    body1 = json.loads(r1.body.decode("utf-8"))
    body2 = json.loads(r2.body.decode("utf-8"))

    # Check if all key-value pairs in body1 are present in body2
    if set(body1.keys()) != set(body2.keys()):
        return False

    for key, value in body1.items():
        if key not in body2 or body2[key] != value:
            return False

    # Check if there are any extra key-value pairs in body2
    for key in body2:
        if key not in body1:
            return False

    return True
