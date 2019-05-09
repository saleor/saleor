"""Django ORM models for Social Auth"""
import six

from django.db import models
from django.conf import settings
from django.db.utils import IntegrityError

from social_core.utils import setting_name

from .compat import get_rel_model
from .storage import DjangoUserMixin, DjangoAssociationMixin, \
                     DjangoNonceMixin, DjangoCodeMixin, \
                     DjangoPartialMixin, BaseDjangoStorage
from .fields import JSONField
from .managers import UserSocialAuthManager


USER_MODEL = getattr(settings, setting_name('USER_MODEL'), None) or \
             getattr(settings, 'AUTH_USER_MODEL', None) or \
             'auth.User'
UID_LENGTH = getattr(settings, setting_name('UID_LENGTH'), 255)
EMAIL_LENGTH = getattr(settings, setting_name('EMAIL_LENGTH'), 254)
NONCE_SERVER_URL_LENGTH = getattr(
    settings, setting_name('NONCE_SERVER_URL_LENGTH'), 255)
ASSOCIATION_SERVER_URL_LENGTH = getattr(
    settings, setting_name('ASSOCIATION_SERVER_URL_LENGTH'), 255)
ASSOCIATION_HANDLE_LENGTH = getattr(
    settings, setting_name('ASSOCIATION_HANDLE_LENGTH'), 255)


class AbstractUserSocialAuth(models.Model, DjangoUserMixin):
    """Abstract Social Auth association model"""
    user = models.ForeignKey(USER_MODEL, related_name='social_auth',
                             on_delete=models.CASCADE)
    provider = models.CharField(max_length=32)
    uid = models.CharField(max_length=UID_LENGTH)
    extra_data = JSONField()
    objects = UserSocialAuthManager()

    def __str__(self):
        return str(self.user)

    class Meta:
        app_label = "social_django"
        abstract = True

    @classmethod
    def get_social_auth(cls, provider, uid):
        try:
            return cls.objects.select_related('user').get(provider=provider,
                                                          uid=uid)
        except cls.DoesNotExist:
            return None

    @classmethod
    def username_max_length(cls):
        username_field = cls.username_field()
        field = cls.user_model()._meta.get_field(username_field)
        return field.max_length

    @classmethod
    def user_model(cls):
        user_model = get_rel_model(field=cls._meta.get_field('user'))
        return user_model


class UserSocialAuth(AbstractUserSocialAuth):
    """Social Auth association model"""

    class Meta:
        """Meta data"""
        app_label = "social_django"
        unique_together = ('provider', 'uid')
        db_table = 'social_auth_usersocialauth'


class Nonce(models.Model, DjangoNonceMixin):
    """One use numbers"""
    server_url = models.CharField(max_length=NONCE_SERVER_URL_LENGTH)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=65)

    class Meta:
        app_label = "social_django"
        unique_together = ('server_url', 'timestamp', 'salt')
        db_table = 'social_auth_nonce'


class Association(models.Model, DjangoAssociationMixin):
    """OpenId account association"""
    server_url = models.CharField(max_length=ASSOCIATION_SERVER_URL_LENGTH)
    handle = models.CharField(max_length=ASSOCIATION_HANDLE_LENGTH)
    secret = models.CharField(max_length=255)  # Stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.CharField(max_length=64)

    class Meta:
        app_label = "social_django"
        db_table = 'social_auth_association'
        unique_together = (
            ('server_url', 'handle',)
        )


class Code(models.Model, DjangoCodeMixin):
    email = models.EmailField(max_length=EMAIL_LENGTH)
    code = models.CharField(max_length=32, db_index=True)
    verified = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "social_django"
        db_table = 'social_auth_code'
        unique_together = ('email', 'code')


class Partial(models.Model, DjangoPartialMixin):
    token = models.CharField(max_length=32, db_index=True)
    next_step = models.PositiveSmallIntegerField(default=0)
    backend = models.CharField(max_length=32)
    data = JSONField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "social_django"
        db_table = 'social_auth_partial'


class DjangoStorage(BaseDjangoStorage):
    user = UserSocialAuth
    nonce = Nonce
    association = Association
    code = Code
    partial = Partial

    @classmethod
    def is_integrity_error(cls, exception):
        return exception.__class__ is IntegrityError
