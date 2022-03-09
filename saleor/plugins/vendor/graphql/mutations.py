import re

import graphene
import phonenumbers
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from phonenumber_field.phonenumber import PhoneNumber

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from ....graphql.core.types import Upload
from ....graphql.core.utils import validate_slug_and_generate_if_needed
from .. import models
from . import enums, types

# from .custom_permissions import BillingPermissions
from .errors import VendorError

numbers_only = re.compile("[0-9]+")


def is_numbers_only(s):
    return numbers_only.match(s)


class VendorInput(graphene.InputObjectType):
    brand_name = graphene.String(description="The name of the brand.", required=True)
    first_name = graphene.String(description="First Name.", required=True)
    last_name = graphene.String(description="Last Name.", required=True)

    slug = graphene.String(
        description="The slug of the vendor. It will be generated if not provided.",
        required=False,
    )

    is_active = graphene.Boolean(
        description="Active status of the vendor.", default_value=True
    )

    description = graphene.JSONString(
        description="Description of the vendor.", required=False
    )

    country = CountryCodeEnum(description="Country code.", required=True)
    users = graphene.List(
        graphene.ID,
        description="Users IDs to add to the vendor.",
    )

    target_gender = enums.TargetGender(
        description="The target gender of the vendor, defaults to UNISEX.",
        default=models.Vendor.TargetGender.UNISEX,  # TODO
        required=False,
    )

    national_id = graphene.String(description="National ID.", required=False)
    residence_id = graphene.String(description="Residence ID.", required=False)

    vat_number = graphene.String(required=False)

    logo = Upload(description="Vendor logo")
    header_image = Upload(required=False, description="Header image.")

    facebook_url = graphene.String(description="Facebook page URL.", required=False)
    instagram_url = graphene.String(description="Instagram page URL.", required=False)
    youtube_url = graphene.String(description="YouTube channel URL.", required=False)
    twitter_url = graphene.String(description="Twitter profile URL.", required=False)


class VendorCreateInput(VendorInput):
    brand_name = graphene.String(description="The name of the brand.", required=True)
    first_name = graphene.String(description="First Name.", required=True)
    last_name = graphene.String(description="Last Name.", required=True)

    phone_number = graphene.String(description="Contact phone number.", required=True)
    email = graphene.String(description="Contact email.", required=True)

    registration_type = enums.RegistrationType(
        description="The registration type of the company.", required=True
    )

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
        errors = {}

        brand_name = data["brand_name"]
        if len(brand_name) == 0:
            errors["brand_name"] = ValidationError(
                "Invalid brand name.",
                code=enums.VendorErrorCode.INVALID_BRAND_NAME,
            )

        else:
            try:
                models.Vendor.objects.get(brand_name=brand_name)
                errors["brand_name"] = ValidationError(
                    message="A vendor with the same name already exists.",
                    code=enums.VendorErrorCode.EXISTING_VENDOR,
                )
            except models.Vendor.DoesNotExist:
                pass

        if len(data["first_name"]) == 0:
            errors["first_name"] = ValidationError(
                "Invalid first name.",
                code=enums.VendorErrorCode.INVALID_FIRST_NAME,
            )

        if len(data["last_name"]) == 0:
            errors["last_name"] = (
                ValidationError(
                    message="Invalid last name.",
                    code=enums.VendorErrorCode.INVALID_LAST_NAME,
                ),
            )

        if email := data.get("email"):
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = ValidationError(
                    "Provided email is invalid.",
                    code=enums.VendorErrorCode.INVALID_EMAIL,
                )

        try:
            phone_number = data["phone_number"]
            PhoneNumber.from_string(phone_number).is_valid()
        except phonenumbers.phonenumberutil.NumberParseException as e:
            errors["phone_number"] = ValidationError(
                str(e), code=enums.VendorErrorCode.INVALID_PHONE_NUMBER
            )

        residence_id = data.get("residence_id")
        national_id = data.get("national_id")

        if residence_id and national_id:
            raise ValidationError(
                message="You must only provide one of residence ID and national ID.",
                code=enums.VendorErrorCode.ONLY_ONE_ALLOWED,
            )

        if not residence_id and not national_id:
            raise ValidationError(
                message="You must provider either residence ID or national ID.",
                code=enums.VendorErrorCode.ONLY_ONE_ALLOWED,
            )

        if residence_id and not is_numbers_only(residence_id):
            errors["residence_id"] = ValidationError(
                message=f"Residence ID must contain only numbers, found: {residence_id}.",  # noqa: E501
                code=enums.VendorErrorCode.INVALID_RESIDENCE_ID,
            )

        if national_id and not is_numbers_only(national_id):
            errors["national_id"] = ValidationError(
                message=f"National ID must contain only numbers, found: {national_id}.",  # noqa: E501
                code=enums.VendorErrorCode.INVALID_NATIONAL_ID,
            )

        registration_type = data["registration_type"]
        if registration_type == enums.RegistrationType.COMPANY:
            vat_number = data.get("vat_number")

            if not vat_number:
                errors["vat_number"] = ValidationError(
                    message="You must provide a VAT for companies.",
                    code=enums.VendorErrorCode.MISSING_VAT,
                )

            elif not is_numbers_only(vat_number):
                errors["vat_number"] = ValidationError(
                    message=f"VAT number must contain only numbers, found: {vat_number}.",  # noqa: E501
                    code=enums.VendorErrorCode.INVALID_VAT,
                )

        registration_number = data["registration_number"]
        if len(registration_number) == 0:
            errors["registration_number"] = ValidationError(
                "Invalid registration number.",
                code=enums.VendorErrorCode.INVALID_REGISTRATION_NUMBER,
            )

        try:
            validate_slug_and_generate_if_needed(instance, "brand_name", cleaned_input)
        except ValidationError as error:
            error.code = enums.VendorErrorCode.INVALID_SLUG
            errors["slug"] = error

        if errors:
            raise ValidationError(errors)

        return cleaned_input


class VendorUpdateInput(VendorInput):
    slug = graphene.String(
        description="The slug of the vendor. It will be generated if not provided.",
        required=False,
    )

    phone_number = graphene.String(description="Contact phone number.", required=False)
    email = graphene.String(description="Contact email.", required=False)

    registration_type = enums.RegistrationType(
        description="The registration type of the company.", required=False
    )
    registration_number = graphene.String(
        description="The registration number.", required=False
    )
    country = CountryCodeEnum(description="Country code.", required=False)


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
        vendor = cls.get_node_or_error(info, data["vendor_id"], only_type=types.Vendor)
        cleaned_input = cls.clean_input(info, vendor, data)
        billing = models.BillingInfo.objects.create(**cleaned_input, vendor=vendor)

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
        # permissions = (BillingPermissions.MANAGE_BILLING,)


class BillingInfoDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Billing information ID.")

    class Meta:
        description = "Delete billing information for a vendor."
        model = models.BillingInfo
        error_type_class = VendorError
        # permissions = (BillingPermissions.MANAGE_BILLING,)


class VendorAddAttachment(ModelMutation):
    class Arguments:
        vendor_id = graphene.ID(required=True, description="Vendor ID.")
        file = Upload(required=True, description="File to be attached")

    class Meta:
        description = "Add an attachment file to the vendor"
        model = models.Attachment
        error_type_class = VendorError

    @classmethod
    def perform_mutation(cls, _root, info, vendor_id, file):
        vendor = cls.get_node_or_error(info, "vendor_id", only_type="Vendor")
        attachment = models.Attachment.objects.create(
            vendor=vendor, file=file
        )  # can be optimized

        return cls(attachment=attachment)


class VendorRemoveAttachment(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID()

    class Meta:
        description = "Remove an attachment from a vendor"
        model = models.Attachment
        error_type_class = VendorError


class VendorUpdateLogo(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        logo = Upload(required=True, description="Logo image.")

    class Meta:
        description = "Update vendor logo image"
        model = models.Vendor
        error_type_class = VendorError

    @classmethod
    def perform_mutation(cls, _root, info, id, logo):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        vendor.logo = logo
        vendor.save()

        return cls(vendor=vendor)


class VendorUpdateHeader(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        header = Upload(required=True, description="Header image.")

    class Meta:
        description = "Update vendor header image"
        model = models.Vendor
        error_type_class = VendorError

    @classmethod
    def perform_mutation(cls, _root, info, id, header):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        vendor.header = header
        vendor.save()

        return cls(vendor=vendor)


class VendorAddProduct(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        product_id = graphene.ID(required=True, description="Product ID.")

    class Meta:
        description = "Add a product to vendor catalogue"
        model = models.Vendor
        error_type_class = VendorError

    @classmethod
    def perform_mutation(cls, _root, info, id, product_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        product = cls.get_node_or_error(info, product_id, only_type="Product")
        vendor.products.add(product)
        info.context.plugins.product_updated(product)
        return cls(vendor=vendor)


class VendorRemoveProduct(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        product_id = graphene.ID(required=True, description="Product ID.")

    class Meta:
        description = "Add a product to vendor catalogue"
        model = models.Vendor
        error_type_class = VendorError

    @classmethod
    def perform_mutation(cls, _root, info, id, product_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        product = cls.get_node_or_error(info, product_id, only_type="Product")
        vendor.products.remove(product)
        info.context.plugins.product_updated(product)
        return cls(vendor=vendor)


class VendorAddUser(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        user_id = graphene.ID(required=True, description="User ID.")

    class Meta:
        description = "Add a user to a vendor."
        model = models.Vendor
        error_type_class = VendorError

    @classmethod
    def perform_mutation(cls, _root, info, id, user_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        user = cls.get_node_or_error(info, user_id, only_type="User")
        vendor.users.add(user)
        return cls(vendor=vendor)


class VendorRemoveUser(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Vendor ID.")
        user_id = graphene.ID(required=True, description="User ID.")

    class Meta:
        description = "Remove a user from a vendor."
        model = models.Vendor
        error_type_class = VendorError

    @classmethod
    def perform_mutation(cls, _root, info, id, user_id):
        vendor = cls.get_node_or_error(info, id, only_type="Vendor")
        user = cls.get_node_or_error(info, user_id, only_type="User")
        vendor.users.remove(user)
        return cls(vendor=vendor)
