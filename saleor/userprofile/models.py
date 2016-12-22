from __future__ import unicode_literals

from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.db import models
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import pgettext_lazy
from django_countries.fields import Country, CountryField
from ..search import index


class AddressManager(models.Manager):

    def as_data(self, address):
        data = model_to_dict(address, exclude=['id', 'user'])
        if isinstance(data['country'], Country):
            data['country'] = data['country'].code
        return data

    def are_identical(self, addr1, addr2):
        data1 = self.as_data(addr1)
        data2 = self.as_data(addr2)
        return data1 == data2

    def store_address(self, user, address):
        data = self.as_data(address)
        address, dummy_created = user.addresses.get_or_create(**data)
        return address


@python_2_unicode_compatible
class Address(models.Model):
    first_name = models.CharField(
        pgettext_lazy('Address field', 'given name'),
        max_length=256, blank=True)
    last_name = models.CharField(
        pgettext_lazy('Address field', 'family name'),
        max_length=256, blank=True)
    company_name = models.CharField(
        pgettext_lazy('Address field', 'company or organization'),
        max_length=256, blank=True)
    street_address_1 = models.CharField(
        pgettext_lazy('Address field', 'address'),
        max_length=256, blank=True)
    street_address_2 = models.CharField(
        pgettext_lazy('Address field', 'address'),
        max_length=256, blank=True)
    city = models.CharField(
        pgettext_lazy('Address field', 'city'),
        max_length=256, blank=True)
    city_area = models.CharField(
        pgettext_lazy('Address field', 'district'),
        max_length=128, blank=True)
    postal_code = models.CharField(
        pgettext_lazy('Address field', 'postal code'),
        max_length=20, blank=True)
    country = CountryField(
        pgettext_lazy('Address field', 'country'))
    country_area = models.CharField(
        pgettext_lazy('Address field', 'state or province'),
        max_length=128, blank=True)
    phone = models.CharField(
        pgettext_lazy('Address field', 'phone number'),
        max_length=30, blank=True)
    objects = AddressManager()

    @property
    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        if self.company_name:
            return '%s - %s' % (self.company_name, self.full_name)
        return self.full_name

    def __repr__(self):
        return (
            'Address(first_name=%r, last_name=%r, company_name=%r, '
            'street_address_1=%r, street_address_2=%r, city=%r, '
            'postal_code=%r, country=%r, country_area=%r, phone=%r)' % (
                self.first_name, self.last_name, self.company_name,
                self.street_address_1, self.street_address_2, self.city,
                self.postal_code, self.country, self.country_area,
                self.phone))


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, is_staff=False,
                    is_active=True, **extra_fields):
        'Creates a User with the given username, email and password'
        email = UserManager.normalize_email(email)
        user = self.model(email=email, is_active=is_active,
                          is_staff=is_staff, **extra_fields)
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        return self.create_user(email, password, is_staff=True,
                                is_superuser=True, **extra_fields)

    def store_address(self, user, address, billing=False, shipping=False):
        entry = Address.objects.store_address(user, address)
        changed = False
        if billing and not user.default_billing_address_id:
            user.default_billing_address = entry
            changed = True
        if shipping and not user.default_shipping_address_id:
            user.default_shipping_address = entry
            changed = True
        if changed:
            user.save()
        return entry


class User(PermissionsMixin, AbstractBaseUser, index.Indexed):
    email = models.EmailField(unique=True)
    addresses = models.ManyToManyField(Address, blank=True)
    is_staff = models.BooleanField(
        pgettext_lazy('User field', 'staff status'),
        default=False)
    is_active = models.BooleanField(
        pgettext_lazy('User field', 'active'),
        default=True)
    date_joined = models.DateTimeField(
        pgettext_lazy('User field', 'date joined'),
        default=timezone.now, editable=False)
    default_shipping_address = models.ForeignKey(
        Address, related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('User field', 'default shipping address'))
    default_billing_address = models.ForeignKey(
        Address, related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('User field', 'default billing address'))

    USERNAME_FIELD = 'email'

    objects = UserManager()

    search_fields = [
        index.SearchField('email')]

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email
