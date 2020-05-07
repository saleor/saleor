import graphene
from graphql_jwt.exceptions import PermissionDenied

from ...core.permissions import AccountPermissions
from ...csv import models
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import Job
from ..utils import get_user_or_app_from_context


class ExportFile(CountableDjangoObjectType):
    url = graphene.String(description="The URL of field to download.")

    class Meta:
        description = "Represents a job data of exported file."
        interfaces = [graphene.relay.Node, Job]
        model = models.ExportFile
        only_fields = ["id", "created_by", "url"]

    @staticmethod
    def resolve_url(root: models.ExportFile, info):
        content_file = root.content_file
        if not content_file:
            return None
        return info.context.build_absolute_uri(content_file.url)

    @staticmethod
    def resolve_created_by(root: models.ExportFile, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor == root.created_by or requestor.has_perm(
            AccountPermissions.MANAGE_USERS
        ):
            return root.created_by
        raise PermissionDenied()
