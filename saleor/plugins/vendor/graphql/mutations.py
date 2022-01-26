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
        description="Is Active to enable or disable the vendor"
    )
    description = graphene.String(description="description of the vendor")
    phone = graphene.String(description="Phone number")
    country = CountryCodeEnum(description="Country")
    users = graphene.List(
        graphene.ID,
        description="Users IDs to add to the vendor",
        name="users",
    )
    commercial_info = enums.CommercialInfo()
    commercial_description = graphene.String(
        description="description of commercial info"
    )
    sells_gender = enums.SellsGender()


class VendorCreateInput(VendorInput):
    name = graphene.String(description="name of the vendor", required=True)
    slug = graphene.String(
        description="Slug of the vendor. Will be generated if not provided",
        required=False,
    )
    national_id = graphene.String(description="national ID", required=True)


class VendorCreate(ModelMutation):
    class Arguments:
        input = VendorCreateInput(
            required=True, description="Fields required to create vendor"
        )

    class Meta:
        description = "create new vendor"
        model = Vendor
        error_type_class = VendorError
        permissions = (VendorPermissions.MANAGE_VENDOR,)

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
    name = graphene.String(description="name of the vendor")
    slug = graphene.String(
        description="Slug of the vendor. Will be generated if not provided",
        required=False,
    )
    national_id = graphene.String(description="national ID")


class VendorUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a vendor to update")
        input = VendorUpdateInput(
            description="Fields required to update a vendor", required=True
        )

    class Meta:
        description = "Update a vendor"
        model = Vendor
        error_type_class = VendorError
        permissions = (VendorPermissions.MANAGE_VENDOR,)


class VendorDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of vendor to delete")

    class Meta:
        description = "delete the vendor"
        model = Vendor
        error_type_class = VendorError
        permissions = (VendorPermissions.MANAGE_VENDOR,)


class BillingCreateInput(graphene.InputObjectType):
    iban_num = graphene.String(
        description="you should enter the real IBAN number", required=True
    )
    bank_name = graphene.String(
        description="bank name related to the IBAN number", required=True
    )


class BillingCreate(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(
            required=True, description="ID of the vendor related to Billing"
        )
        input = BillingCreateInput(
            required=True, description="Fields required to create billing"
        )

    class Meta:
        description = "Create New Billing"
        model = Billing
        error_type_class = BillingError
        permissions = (BillingPermissions.MANAGE_BILLING,)

    @classmethod
    def clean_input(cls, info, instance, data):
        validation_errors = {}
        for field in ["iban_num", "bank_name"]:
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
        # print(billing.vendor)
        # print(billing)
        # return cls()
        billing.save()
        return BillingCreate(billing=billing)


class BillingUpdateInput(graphene.InputObjectType):
    iban_num = graphene.String(description="you should enter the real IBAN number")
    bank_name = graphene.String(description="bank name related to the IBAN number")


class BillingUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a Billing to update")
        input = BillingUpdateInput(
            description="Fields required to update a Billing", required=True
        )

    class Meta:
        description = "Update a Billing"
        model = Billing
        error_type_class = BillingError
        permissions = (BillingPermissions.MANAGE_BILLING,)


class BillingDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of Billing to delete")

    class Meta:
        description = "delete the Billing"
        model = Billing
        error_type_class = BillingError
        permissions = (BillingPermissions.MANAGE_BILLING,)
