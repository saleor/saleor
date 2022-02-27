from django.db import models
from django_countries.fields import CountryField
from django_iban.fields import IBANField
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth import get_user_model
from ...account.validators import validate_possible_number


User = get_user_model()


class PossiblePhoneNumberField(PhoneNumberField):
    # """Less strict field for phone numbers written to database"""

    default_validators = [validate_possible_number]


class Vendor(models.Model):
    class CommercialInfoChoices(models.IntegerChoices):
        CR = 1
        MAROOF = 2

    class TargetGenderChoices(models.IntegerChoices):
        MEN = 1
        WOMEN = 2
        UNISEX = 3

    name = models.CharField(max_length=256, unique=True, db_index=True)
    slug = models.SlugField(max_length=256, unique=True, db_index=True)
    users = models.ManyToManyField(User)
    country = CountryField()

    description = models.TextField(blank=True, default="")
    phone_number = PossiblePhoneNumberField(blank=True, db_index=True)

    national_id = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    commercial_info = models.IntegerField(
        choices=CommercialInfoChoices.choices, default=CommercialInfoChoices.CR
    )
    commercial_description = models.TextField(blank=True, default="")
    target_gender = models.IntegerField(
        choices=TargetGenderChoices.choices, default=TargetGenderChoices.UNISEX
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BillingInfo(models.Model):
    iban = IBANField()
    bank_name = models.CharField(max_length=256)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="billing_info")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
