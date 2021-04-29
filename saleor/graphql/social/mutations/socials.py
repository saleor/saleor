import graphene

from ....social import models
from ...core.mutations import ModelMutation
from ...core.types.common import SocialError
from ....core.permissions import SocialPermissions
from ...store.types import Store

class SocialInput(graphene.InputObjectType):
    follow = graphene.Boolean(description="follow/unfollow action.")
    store = graphene.ID(
        required=True, description="ID of a following store.", name="store"
    )    

class SocialCreate(ModelMutation):
    store = graphene.Field(Store)

    class Arguments:
        input = SocialInput(
            required=True, description="Fields required to follow/unfollow."
        )

    class Meta:
        description = "Follow/unfollow a store."
        model = models.Social
        permissions = (SocialPermissions.MANAGE_SOCIALS,)
        error_type_class = SocialError
        error_type_field = "social_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        data["input"]["user_id"] = graphene.Node.to_global_id("User", user.id)
        return super().perform_mutation(root, info, **data)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

