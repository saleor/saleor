import graphene
from graphene import relay
from graphene_federation import key
from graphql_jwt.exceptions import PermissionDenied

from ...core.permissions import AccountPermissions
from ...csv import models
from ..core.connection import CountableDjangoObjectType


@key(fields="id")
class Job(CountableDjangoObjectType):
    url = graphene.String(description="The URL of field to download.")
    status = graphene.String(description="Job status.")

    class Meta:
        description = "Represents job data"
        interfaces = [relay.Node]
        model = models.Job
        only_fields = ["id", "created_at", "ended_at", "status", "url", "user"]

    @staticmethod
    def resolve_url(root: models.Job, _info):
        content_file = root.content_file
        if not content_file:
            return None
        return _info.context.build_absolute_uri(content_file.url)

    @staticmethod
    def resolve_status(root: models.Job, _info):
        return root.status.split(".")[1]

    @staticmethod
    def resolve_user(root: models.Job, info):
        user = info.context.user
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_USERS):
            return root.user
        raise PermissionDenied()
