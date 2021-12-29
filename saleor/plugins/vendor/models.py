from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from saleor.account.validators import validate_possible_number


class PossiblePhoneNumberField(PhoneNumberField):
    # """Less strict field for phone numbers written to database"""

    default_validators = [validate_possible_number]


class Vendor(models.Model):
    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        (
            "U",
            "Unsure",
        ),
    )
    name = models.CharField(max_length=256, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    description = models.TextField(blank=True, default="")
    country = CountryField()
    phone = PossiblePhoneNumberField(blank=True, default="", db_index=True)
    national_id = models.CharField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    birth_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
