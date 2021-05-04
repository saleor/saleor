import graphene

from .types import Social
from ..core.fields import FilterInputConnectionField
from .mutations.socials import (
    SocialCreate,
)
from .resolvers import (
    resolve_social,
    resolve_socials,
)

class SocialQueries(graphene.ObjectType):
    social = FilterInputConnectionField(
        Social,
        description="List of the follow by user.",
    )

    socials = FilterInputConnectionField(
        Social,
        description="List all of the follow.",
    )

    def resolve_social(self, info, id=None, slug=None):
        return resolve_social(info, id, slug)

    def resolve_socials(self, info, **kwargs):
        return resolve_socials(info, **kwargs)



class SocialMutations(graphene.ObjectType):
    # social mutations
    social_create = SocialCreate.Field()