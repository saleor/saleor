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
    social = graphene.Field(
        Social,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the post.",
        ),
        description="Look up a post by ID.",
    )

    socials = FilterInputConnectionField(
        Social,
        description="List of the post.",
    )    

    def resolve_social(self, info, slug=None):
        return resolve_social(info, slug)

    def resolve_socials(self, info, **kwargs):
        return resolve_socials(info, **kwargs)



class SocialMutations(graphene.ObjectType):
    # social mutations
    social_create = SocialCreate.Field()