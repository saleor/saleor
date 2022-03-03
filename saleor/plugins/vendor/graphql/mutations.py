import graphene
from django.core.exceptions import ValidationError

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from ....graphql.core.types import Upload
from ....graphql.core.utils import validate_slug_and_generate_if_needed
from .. import models
from . import enums, types
from .custom_permissions import BillingPermissions
from .errors import VendorError


class VendorInput(graphene.InputObjectType):
    is_active = graphene.Boolean(
        description="Active status of the vendor.", default_value=True
    )
    description = graphene.String(description="Description of the vendor.")
    phone_number = graphene.String(description="Phone number.")
    country = CountryCodeEnum(description="Country code.")
    users = graphene.List(
        graphene.ID,
        description="Users IDs to add to the vendor.",
    )
    registration_type = enums.RegistrationTypeEnum(
        required=True, description="The registration type of the company."
    )
    target_gender = enums.TargetGenderEnum(
        required=False,
        description="The target gender of the vendor, defaults to UNISEX.",
    )

    national_id = graphene.String(required=False, description="National ID.")
    residence_id = graphene.String(required=False, description="Residence ID.")

    vat_number = graphene.String(required=False)

    logo = Upload(description="Vendor logo")
    header_image = Upload(required=False, description="Header image.")


class VendorCreateInput(VendorInput):
    name = graphene.String(description="The name of the vendor.", required=True)
    slug = graphene.String(
        description="The slug of the vendor. It will be generated if not provided.",
        required=False,
    )
    national_id = graphene.String(description="National ID.", required=True)
    registration_number = graphene.String(
        required=True, description="The registration number."
    )


class VendorCreate(ModelMutation):
    class Arguments:
        input = VendorCreateInput(
            required=True, description="Fields required to create a vendor."
        )

    class Meta:
        description = "Create a new vendor."
        model = models.Vendor
        error_type_class = VendorError
        # permissions = (VendorPermissions.MANAGE_VENDOR,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = enums.VendorErrorCode.VENDOR_SLUG.value
            raise ValidationError({"slug": error})
        return cleaned_input


class VendorUpdateInput(VendorInput):
    name = graphene.String(description="The name of the vendor.")
    slug = graphene.String(
        description="The slug of the vendor. It will be generated if not provided.",
        required=False,
    )
    national_id = graphene.String(description="National ID.")

    national_id = graphene.String(required=False, description="National ID")
    registration_number = graphene.String(
        required=False, description="The registration number."
    )


class VendorUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        input = VendorUpdateInput(
            description="Fields required to update the vendor.", required=True
        )

    class Meta:
        description = "Update a vendor."
        model = models.Vendor
        error_type_class = VendorError
        # permissions = (VendorPermissions.MANAGE_VENDOR,)


class VendorDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")

    class Meta:
        description = "Delete the vendor."
        model = models.Vendor
        error_type_class = VendorError
        # permissions = (VendorPermissions.MANAGE_VENDOR,)


class BillingInfoCreateInput(graphene.InputObjectType):
    iban = graphene.String(description="IBAN number of the vendor.", required=True)
    bank_name = graphene.String(description="The bank name.", required=True)


class BillingInfoCreate(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(required=True, description="Vendor ID.")
        input = BillingInfoCreateInput(
            required=True,
            description="Fields required to add billing information to the vendor.",
        )

    class Meta:
        description = "Create a new billing information for a vendor."
        model = models.BillingInfo
        error_type_class = VendorError
        # permissions = (BillingPermissions.MANAGE_BILLING,)

    @classmethod
    def clean_input(cls, info, instance, data):
        validation_errors = {}
        for field in ["iban", "bank_name"]:
            if data["input"][field] == "":
                validation_errors[field] = ValidationError(
                    f"{field} cannot be empty.",
                    code=enums.BillingErrorCode.BILLING_ERROR,
                )
        if validation_errors:
            raise ValidationError(validation_errors)
        return data["input"]

    @classmethod
    def perform_mutation(cls, root, info, **data):
        vendor = cls.get_node_or_error(
            info, data["vendor_id"], only_type=types.Vendor, field="vendorId"
        )
        cleaned_input = cls.clean_input(info, vendor, data)
        billing = models.BillingInfo(**cleaned_input)
        billing.vendor = vendor
        billing.save()

        return cls(billing=billing)


class BillingInfoUpdateInput(graphene.InputObjectType):
    iban = graphene.String(description="IBAN number of the vendor.")
    bank_name = graphene.String(description="The bank name.")


class BillingInfoUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Billing information ID.")
        input = BillingInfoUpdateInput(
            description="Fields required to update billing information.", required=True
        )

    class Meta:
        description = "Update billing information."
        model = models.BillingInfo
        error_type_class = VendorError
        permissions = (BillingPermissions.MANAGE_BILLING,)


class BillingInfoDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Billing information ID.")

    class Meta:
        description = "Delete billing information for a vendor."
        model = models.BillingInfo
        error_type_class = VendorError
        # permissions = (BillingPermissions.MANAGE_BILLING,)
