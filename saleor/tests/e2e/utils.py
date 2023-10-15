from ...account.models import Group
from ...graphql.tests.utils import get_graphql_content  # noqa: F401
from ...graphql.tests.utils import get_multipart_request_body  # noqa: F401


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
