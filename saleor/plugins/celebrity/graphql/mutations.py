import graphene
import phonenumbers
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from phonenumber_field.phonenumber import PhoneNumber

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from ....graphql.core.types import Upload
from .. import models
from . import enums
from .errors import CelebrityError


class CelebrityInput(graphene.InputObjectType):
    is_active = graphene.Boolean(
        description="Active status of the Celebrity.", default_value=True
    )
    phone_number = graphene.String(description="Phone number.")
    email = graphene.String(description="Phone number.")
    country = CountryCodeEnum(description="Country code.")
    city = graphene.String(description="City of the Celebrity.")
    website_url = graphene.String(description="Website of the Celebrity.")
    instagram_url = graphene.String(description="Instagram Link of the Celebrity.")
    twitter_url = graphene.String(description="Twitter Link of the Celebrity.")
    bio = graphene.String(description="Bio of the Celebrity.")
    about = graphene.String(description="about of the Celebrity.")

    variants = graphene.List(
        graphene.ID,
        description="Product Variant IDs to add to the celebrity.",
    )

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

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        errors = {}

        if len(data["first_name"]) == 0:
            errors["first_name"] = ValidationError(
                "Invalid first name.",
                code=enums.CelebrityErrorCode.INVALID_FIRST_NAME,
            )

        if len(data["last_name"]) == 0:
            errors["last_name"] = (
                ValidationError(
                    message="Invalid last name.",
                    code=enums.CelebrityErrorCode.INVALID_LAST_NAME,
                ),
            )

        if email := data.get("email"):
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = ValidationError(
                    "Provided email is invalid.",
                    code=enums.CelebrityErrorCode.INVALID_EMAIL,
                )

        try:
            phone_number = data["phone_number"]
            PhoneNumber.from_string(phone_number).is_valid()
        except phonenumbers.phonenumberutil.NumberParseException as e:
            errors["phone_number"] = ValidationError(
                str(e), code=enums.CelebrityErrorCode.INVALID_PHONE_NUMBER
            )

        if errors:
            raise ValidationError(errors)

        return cleaned_input


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


class CelebrityUpdateLogo(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="celebrity ID.")
        logo = Upload(required=True, description="Logo image.")

    class Meta:
        description = "Update celebrity logo image"
        model = models.Celebrity
        error_type_class = CelebrityError

    @classmethod
    def perform_mutation(cls, _root, info, id, logo):
        celebrity = cls.get_node_or_error(info, id, only_type="Celebrity")
        celebrity.logo = logo
        celebrity.save()

        return cls(celebrity=celebrity)


class CelebrityUpdateHeader(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Celebrity ID.")
        header = Upload(required=True, description="Header image.")

    class Meta:
        description = "Update Celebrity header image"
        model = models.Celebrity
        error_type_class = CelebrityError

    @classmethod
    def perform_mutation(cls, _root, info, id, header):
        celebrity = cls.get_node_or_error(info, id, only_type="Celebrity")
        celebrity.header = header
        celebrity.save()

        return cls(celebrity=celebrity)
