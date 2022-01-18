from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from django_iban.fields import IBANField
from phonenumber_field.modelfields import PhoneNumberField

from saleor.account.validators import validate_possible_number


class PossiblePhoneNumberField(PhoneNumberField):
    # """Less strict field for phone numbers written to database"""

    default_validators = [validate_possible_number]


class Vendor(models.Model):

    name = models.CharField(max_length=256, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    description = models.TextField(blank=True, default="")
    country = CountryField()
    phone = PossiblePhoneNumberField(blank=True, default="", db_index=True)
    national_id = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Billing(models.Model):
    iban_num = IBANField()
    bank_name = models.CharField(max_length=256)
    vendors = models.ForeignKey(Vendor, blank=True, null=True, on_delete=models.CASCADE)
