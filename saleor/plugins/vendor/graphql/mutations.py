import graphene
from django.core.exceptions import ValidationError

from saleor.graphql.account.enums import CountryCodeEnum

from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from ....graphql.core.utils import validate_slug_and_generate_if_needed
from ..models import Billing, Vendor
from . import enums, types
from .custom_permissions import BillingPermissions, VendorPermissions
from .errors import BillingError, VendorError


class VendorInput(graphene.InputObjectType):
    is_active = graphene.Boolean(
        description="Active status of the vendor."
    )
    description = graphene.String(description="Description of the vendor.")
    phone = graphene.String(description="Phone number.")
    country = CountryCodeEnum(description="Country code.")
    users = graphene.List(
        graphene.ID,
        description="Users IDs to add to the vendor.",
        name="users",
    )
    commercial_info = enums.CommercialInfo()
    commercial_description = graphene.String(
        description="description of commercial info."
    )
    sells_gender = enums.SellsGender()


class VendorCreateInput(VendorInput):
    name = graphene.String(description="The name of the vendor.", required=True)
    slug = graphene.String(
        description="The slug of the vendor. It will be generated if not provided.",
        required=False,
    )
    national_id = graphene.String(description="National ID.", required=True)


class VendorCreate(ModelMutation):
    class Arguments:
        input = VendorCreateInput(
            required=True, description="Fields required to create a vendor."
        )

    class Meta:
        description = "Create a new vendor."
        model = Vendor
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


class VendorUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        input = VendorUpdateInput(
            description="Fields required to update the vendor.", required=True
        )

    class Meta:
        description = "Update a vendor."
        model = Vendor
        error_type_class = VendorError
        # permissions = (VendorPermissions.MANAGE_VENDOR,)


class VendorDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")

    class Meta:
        description = "Delete the vendor."
        model = Vendor
        error_type_class = VendorError
        # permissions = (VendorPermissions.MANAGE_VENDOR,)


class BillingCreateInput(graphene.InputObjectType):
    iban = graphene.String(
        description="IBAN number of the vendor.", required=True
    )
    bank_name = graphene.String(
        description="The bank name.", required=True
    )


class BillingCreate(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(
            required=True, description="Vendor ID."
        )
        input = BillingCreateInput(
            required=True, description="Fields required to add billing information to the vendor."
        )

    class Meta:
        description = "Create a new billing information for a vendor."
        model = Billing
        error_type_class = BillingError
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
        billing = Billing(**cleaned_input)
        billing.vendor = vendor
        billing.save()

        return cls(billing=billing)


class BillingUpdateInput(graphene.InputObjectType):
    iban = graphene.String(description="IBAN number of the vendor.")
    bank_name = graphene.String(description="The bank name.")


class BillingUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Billing information ID.")
        input = BillingUpdateInput(
            description="Fields required to update billing information.", required=True
        )

    class Meta:
        description = "Update billing information."
        model = Billing
        error_type_class = BillingError
        permissions = (BillingPermissions.MANAGE_BILLING,)


class BillingDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Billing information ID.")

    class Meta:
        description = "Delete billing information for a vendor."
        model = Billing
        error_type_class = BillingError
        # permissions = (BillingPermissions.MANAGE_BILLING,)
