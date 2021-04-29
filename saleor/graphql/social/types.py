import graphene

from graphene_federation import key
from ...social import models
from ..core.connection import CountableDjangoObjectType


class Social(CountableDjangoObjectType):
    follow = graphene.Boolean(
        description="follow action.",
        required=True,
    )
    
    class Meta:
        description = (
            "social follow action."
        )
        only_fields = [
            "follow",
        ]
        model = models.Social
