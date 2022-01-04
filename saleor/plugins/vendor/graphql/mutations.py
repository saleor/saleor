import graphene

from saleor.graphql.account.enums import CountryCodeEnum
from saleor.plugins.vendor.graphql.enums import GenderCodeEnum

from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from ..models import Vendor
from .custom_permissions import VendorPermissions
from .errors import VendorError


class VendorInput(graphene.InputObjectType):
    is_active = graphene.Boolean(
        description="Is Active to enable or disable the vendor"
    )
    description = graphene.String(description="description of the vendor")
    phone = graphene.String(description="Phone number")
    country = CountryCodeEnum(description="Country")
    national_id = graphene.String(description="national ID")
    birth_date = graphene.DateTime(description="Birth Day")
    gender = graphene.Field(GenderCodeEnum, description="gender")
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
    name = graphene.String(description="name of the vendor", required=True)
    slug = graphene.String(
        description="Slug of the vendor. Will be generated if not provided",
        required=False,
    )


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
