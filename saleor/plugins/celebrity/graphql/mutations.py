import graphene

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from ....graphql.core.types import Upload
from .. import models
from .errors import CelebrityError


class CelebrityInput(graphene.InputObjectType):
    is_active = graphene.Boolean(
        description="Active status of the Celebrity.", default_value=True
    )
    phone_number = graphene.String(description="Phone number.")
    email = graphene.String(description="Phone number.")
    country = CountryCodeEnum(description="Country code.")
    city = graphene.String(description="City of the Celebrity.")
    website = graphene.String(description="Website of the Celebrity.")
    instagram_link = graphene.String(description="Instagram Link of the Celebrity.")
    twitter_link = graphene.String(description="Twitter Link of the Celebrity.")
    bio = graphene.String(description="Bio of the Celebrity.")
    about = graphene.String(description="about of the Celebrity.")

    logo = Upload(description="Celebrity logo")
    header_image = Upload(required=False, description="Header image.")


class CelebrityCreateInput(CelebrityInput):
    first_name = graphene.String(
        description="The first name of the Celebrity.", required=True
    )
    last_name = graphene.String(
        description="The last name of the Celebrity.", required=True
    )
    phone_number = graphene.String(description="Phone number.", required=True)
    email = graphene.String(description="Phone number.", required=True)


class CelebrityCreate(ModelMutation):
    class Arguments:
        input = CelebrityCreateInput(
            required=True, description="Fields required to create a Celebrity."
        )

    class Meta:
        description = "Create a new Celebrity."
        model = models.Celebrity
        error_type_class = CelebrityError
        # permissions = (CelebrityPermissions.MANAGE_CELEBRITY,)


class CelebrityUpdateInput(CelebrityInput):
    first_name = graphene.String(description="The first name of the Celebrity.")
    last_name = graphene.String(description="The last name of the Celebrity.")


class CelebrityUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Celebrity ID.")
        input = CelebrityUpdateInput(
            description="Fields required to update the Celebrity.", required=True
        )

    class Meta:
        description = "Update a Celebrity."
        model = models.Celebrity
        error_type_class = CelebrityError
        # permissions = (CelebrityPermissions.MANAGE_CELEBRITY,)


class CelebrityDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Celebrity ID.")

    class Meta:
        description = "Delete the Celebrity."
        model = models.Celebrity
        error_type_class = CelebrityError
        # permissions = (CelebrityPermissions.MANAGE_CELEBRITY,)
