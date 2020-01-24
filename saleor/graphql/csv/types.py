import graphene
from graphene import relay
from graphene_federation import key

from ...csv import models
from ..core.connection import CountableDjangoObjectType


@key(fields="id")
class Job(CountableDjangoObjectType):
    url = graphene.String(description="The URL of field to download.")

    class Meta:
        description = "Represents job data"
        interfaces = [relay.Node]
        model = models.Job
        only_fields = ["id", "created_at", "status", "url"]

    @staticmethod
    def resolve_url(root: models.Job, _info):
        return root.content_file.url if root.content_file else ""
