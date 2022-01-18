import graphene

from saleor.graphql.account.enums import CountryCodeEnum

from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from ..models import Billing, Vendor
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
        permutations = (VendorPermissions.MANAGE_VENDOR,)


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


# mutations for Billing
class BillingCreateInput(graphene.InputObjectType):
    iban_num = graphene.String(
        description="you should enter the real IBAN number", required=True
    )
    bank_name = graphene.String(
        description="bank name related to the IBAN number", required=True
    )
    vendors = graphene.List(
        graphene.ID,
        description="vendors IDs to add to billing information",
        name="vendors",
    )


class BillingCreate(ModelMutation):
    class Arguments:
        input = BillingCreateInput(
            required=True, description="Fields required to create billing"
        )

    class Meta:
        description = "Create New Billing"
        model = Billing
        error_type_class = BillingError
        permissions = (BillingPermissions.MANAGE_BILLING,)


class BillingUpdateInput(graphene.InputObjectType):
    iban_num = graphene.String(description="you should enter the real IBAN number")
    bank_name = graphene.String(description="bank name related to the IBAN number")
    vendors = graphene.List(
        graphene.ID,
        description="vendors IDs to add to billing information",
        name="vendors",
    )


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
