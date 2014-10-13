from __future__ import unicode_literals
import re

from django.contrib.auth.hashers import (check_password, make_password,
                                         is_password_usable)
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.db import models
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy
from unidecode import unidecode

from ..core.countries import COUNTRY_CHOICES


class AddressBookManager(models.Manager):

    def store_address(self, user, address, alias):
        data = Address.objects.as_data(address)
        query = dict(('address__%s' % (key,), value)
                     for key, value in data.items())
        candidates = self.get_queryset().filter(user=user, **query)
        candidates = candidates.select_for_update()
        try:
            entry = candidates[0]
        except IndexError:
            address = Address.objects.create(**data)
            entry = AddressBook.objects.create(user=user, address=address,
                                               alias=alias)
        return entry


@python_2_unicode_compatible
class AddressBook(models.Model):

    user = models.ForeignKey('User', related_name='address_book')
    address = models.ForeignKey('Address', related_name='+', unique=True)
    alias = models.CharField(
        pgettext_lazy('Address book entry', 'short alias'),
        max_length=30,
        default='Home',
        help_text=pgettext_lazy(
            'Address book entry',
            'A short, descriptive name for this address'))

    objects = AddressBookManager()

    class Meta:
        unique_together = ('user', 'alias')

    def __str__(self):
        return self.alias

    @models.permalink
    def get_absolute_url(self):
        return ('profile:address-edit',
                (),
                {'slug': self.get_slug(), 'pk': self.id})

    def get_slug(self):
        value = unidecode(self.alias)
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()

        return mark_safe(re.sub(r'[-\s]+', '-', value))


class AddressManager(models.Manager):

    def as_data(self, addr):
        return model_to_dict(addr, exclude=['id', 'user'])

    def are_identical(self, addr1, addr2):
        data1 = self.as_data(addr1)
        data2 = self.as_data(addr2)
        return data1 == data2


@python_2_unicode_compatible
class Address(models.Model):

    first_name = models.CharField(
        pgettext_lazy('Address field', 'first name'),
        max_length=256)
    last_name = models.CharField(
        pgettext_lazy('Address field', 'last name'),
        max_length=256)
    company_name = models.CharField(
        pgettext_lazy('Address field', 'company name'),
        max_length=256, blank=True)
    street_address_1 = models.CharField(
        pgettext_lazy('Address field', 'street address 1'),
        max_length=256)
    street_address_2 = models.CharField(
        pgettext_lazy('Address field', 'street address 2'),
        max_length=256, blank=True)
    city = models.CharField(
        pgettext_lazy('Address field', 'city'),
        max_length=256)
    postal_code = models.CharField(
        pgettext_lazy('Address field', 'postal code'),
        max_length=20)
    country = models.CharField(
        pgettext_lazy('Address field', 'country'),
        choices=COUNTRY_CHOICES, max_length=2)
    country_area = models.CharField(
        pgettext_lazy('Address field', 'country administrative area'),
        max_length=128, blank=True)
    phone = models.CharField(
        pgettext_lazy('Address field', 'phone number'),
        max_length=30, blank=True)

    objects = AddressManager()

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

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

    def get_or_create(self, **kwargs):
        defaults = kwargs.pop('defaults', {})
        try:
            return self.get_query_set().get(**kwargs), False
        except self.model.DoesNotExist:
            defaults.update(kwargs)
            return self.create_user(**defaults), True

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

    def store_address(self, user, address, alias,
                      billing=False, shipping=False):
        entry = AddressBook.objects.store_address(user, address, alias)
        changed = False
        if billing and not user.default_billing_address_id:
            user.default_billing_address = entry
            changed = True
        if shipping and not user.default_shipping_address_id:
            user.default_shipping_address = entry
            changed = True
        if changed:
            user.save()


@python_2_unicode_compatible
class User(PermissionsMixin, models.Model):
    email = models.EmailField(unique=True)

    addresses = models.ManyToManyField(Address, through=AddressBook)

    is_staff = models.BooleanField(
        pgettext_lazy('User field', 'staff status'),
        default=False)
    is_active = models.BooleanField(
        pgettext_lazy('User field', 'active'),
        default=False)
    password = models.CharField(
        pgettext_lazy('User field', 'password'),
        max_length=128, editable=False)
    date_joined = models.DateTimeField(
        pgettext_lazy('User field', 'date joined'),
        default=timezone.now, editable=False)
    last_login = models.DateTimeField(
        pgettext_lazy('User field', 'last login'),
        default=timezone.now, editable=False)
    default_shipping_address = models.ForeignKey(
        AddressBook, related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('User field', 'default shipping address'))
    default_billing_address = models.ForeignKey(
        AddressBook, related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('User field', 'default billing address'))

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.get_username()

    def natural_key(self):
        return (self.get_username(),)

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def get_username(self):
        'Return the identifying username for this User'
        return self.email

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=['password'])
        return check_password(raw_password, self.password, setter)

    def set_unusable_password(self):
        self.password = make_password(None)

    def has_usable_password(self):
        return is_password_usable(self.password)
