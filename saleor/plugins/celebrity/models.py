from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from ...account.validators import validate_possible_number
from ...product.models import Product


class PossiblePhoneNumberField(PhoneNumberField):
    default_validators = [validate_possible_number]


class Celebrity(models.Model):

    first_name = models.CharField(max_length=256, db_index=True)
    last_name = models.CharField(max_length=256, db_index=True)
    phone_number = PossiblePhoneNumberField(db_index=True, unique=True)
    email = models.EmailField(unique=True)
    country = CountryField()
    city = models.CharField(max_length=256, blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    is_active = models.BooleanField()
    logo = models.ImageField(blank=True, null=True)
    header_image = models.ImageField(blank=True, null=True)
    products = models.ManyToManyField(Product)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
