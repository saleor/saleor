from __future__ import unicode_literals
from datetime import timedelta
from uuid import uuid4

from django.db import models
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone

now = timezone.now


def default_valid_date():
    return now() + timedelta(settings.ACCOUNT_ACTIVATION_DAYS)


class ExternalUserData(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='external_ids')
    service = models.CharField(db_index=True, max_length=255)
    username = models.CharField(db_index=True, max_length=255)

    class Meta:
        unique_together = [['service', 'username']]


class UniqueTokenManager(models.Manager):  # this might end up in `utils`
    def __init__(self, token_field):
        self.token_field = token_field
        super(UniqueTokenManager, self).__init__()

    def create(self, **kwargs):
        assert self.token_field not in kwargs, 'Token field already filled.'
        kwargs[self.token_field] = str(uuid4())
        return super(UniqueTokenManager, self).create(**kwargs)


class AbstractToken(models.Model):
    token = models.CharField(max_length=36, unique=True)
    valid_until = models.DateTimeField(default=default_valid_date)

    objects = UniqueTokenManager(token_field='token')

    class Meta:
        abstract = True


class EmailConfirmationRequest(AbstractToken):
    email = models.EmailField()

    def get_authenticated_user(self):
        user, dummy_created = get_user_model().objects.get_or_create(
            email=self.email)
        return authenticate(user=user)

    def get_confirmation_url(self):
        return reverse('registration:confirm_email',
                       kwargs={'token': self.token})


class EmailChangeRequest(AbstractToken):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='email_change_requests')
    email = models.EmailField()  # email address that user is switching to

    def get_confirmation_url(self):
        return reverse('registration:change_email',
                       kwargs={'token': self.token})
