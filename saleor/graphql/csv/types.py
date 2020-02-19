import graphene
from graphene import relay
from graphene_federation import key
from graphql_jwt.exceptions import PermissionDenied

from ...core.permissions import AccountPermissions
from ...csv import models
from ..core.connection import CountableDjangoObjectType
from .enums import JobStatusEnum


@key(fields="id")
class Job(CountableDjangoObjectType):
    url = graphene.String(description="The URL of field to download.")
    status = JobStatusEnum(description="Job status.")

    class Meta:
        description = "Represents job data"
        interfaces = [relay.Node]
        model = models.Job
        only_fields = [
            "id",
            "created_at",
            "completed_at",
            "status",
            "url",
            "created_by",
        ]

    @staticmethod
    def resolve_url(root: models.Job, info):
        content_file = root.content_file
        if not content_file:
            return None
        return info.context.build_absolute_uri(content_file.url)

    @staticmethod
    def resolve_status(root: models.Job, _info):
        return root.status

    @staticmethod
    def resolve_created_by(root: models.Job, info):
        user = info.context.user
        if user == root.created_by or user.has_perm(AccountPermissions.MANAGE_USERS):
            return root.created_by
        raise PermissionDenied()
