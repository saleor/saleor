from django.contrib.auth import get_user_model
from django.db import models
from django_countries.fields import CountryField
from django_iban.fields import IBANField
from phonenumber_field.modelfields import PhoneNumberField

from ...account.validators import validate_possible_number
from ...core.db.fields import SanitizedJSONField
from ...core.utils.editorjs import clean_editor_js
from ...product.models import ProductVariant

User = get_user_model()


class PossiblePhoneNumberField(PhoneNumberField):
    # """Less strict field for phone numbers written to database"""

    default_validators = [validate_possible_number]


class Vendor(models.Model):
    class RegistrationType(models.IntegerChoices):
        COMPANY = 1
        MAROOF = 2

    class TargetGender(models.IntegerChoices):
        MEN = 1
        WOMEN = 2
        UNISEX = 3

    name = models.CharField(max_length=256, unique=True, db_index=True)
    slug = models.SlugField(max_length=256, unique=True, db_index=True)
    users = models.ManyToManyField(User)
    variants = models.ManyToManyField(ProductVariant)

    country = CountryField()

    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    phone_number = PossiblePhoneNumberField(blank=True, db_index=True)

    national_id = models.CharField(max_length=256, null=True, blank=True)
    residence_id = models.CharField(max_length=256, null=True, blank=True)

    is_active = models.BooleanField()
    registration_type = models.IntegerField(
        choices=RegistrationType.choices, default=RegistrationType.COMPANY
    )
    registration_number = models.CharField(max_length=256)
    vat_number = models.CharField(max_length=256, blank=True, null=True)

    target_gender = models.IntegerField(
        choices=TargetGender.choices, default=TargetGender.UNISEX
    )

    logo = models.ImageField(blank=True, null=True)
    header_image = models.ImageField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)


class BillingInfo(models.Model):
    iban = IBANField()
    bank_name = models.CharField(max_length=256)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="billing_info"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Attachment(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField()

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
