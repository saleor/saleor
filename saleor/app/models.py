from collections.abc import Iterable
from typing import Union, cast
from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils.text import Truncator
from oauthlib.common import generate_token

from ..core.models import Job, ModelWithMetadata
from ..permission.enums import AppPermission, BasePermissionEnum
from ..permission.models import Permission
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .types import AppExtensionMount, AppExtensionTarget, AppType


class AppQueryset(models.QuerySet["App"]):
    def for_event_type(self, event_type: str):
        permissions = {}
        required_permission = WebhookEventAsyncType.PERMISSIONS.get(
            event_type, WebhookEventSyncType.PERMISSIONS.get(event_type)
        )
        if required_permission:
            app_label, codename = required_permission.value.split(".")
            permissions["permissions__content_type__app_label"] = app_label
            permissions["permissions__codename"] = codename
        return self.filter(
            is_active=True,
            webhooks__is_active=True,
            webhooks__events__event_type=event_type,
            **permissions,
        )


AppManager = models.Manager.from_queryset(AppQueryset)


class App(ModelWithMetadata):
    uuid = models.UUIDField(unique=True, default=uuid4)
    name = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    removed_at = models.DateTimeField(blank=True, null=True)
    type = models.CharField(
        choices=AppType.CHOICES, default=AppType.LOCAL, max_length=60
    )
    identifier = models.CharField(max_length=256, blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Specific permissions for this app.",
        related_name="app_set",
        related_query_name="app",
    )
    about_app = models.TextField(blank=True, null=True)
    data_privacy = models.TextField(blank=True, null=True)
    data_privacy_url = models.URLField(blank=True, null=True)
    homepage_url = models.URLField(blank=True, null=True)
    support_url = models.URLField(blank=True, null=True)
    configuration_url = models.URLField(blank=True, null=True)
    app_url = models.URLField(blank=True, null=True)
    manifest_url = models.URLField(blank=True, null=True)
    version = models.CharField(max_length=60, blank=True, null=True)
    audience = models.CharField(blank=True, null=True, max_length=256)
    is_installed = models.BooleanField(default=True)
    author = models.CharField(blank=True, null=True, max_length=60)
    brand_logo_default = models.ImageField(
        upload_to="app-brand-data", blank=True, null=True
    )
    objects = AppManager()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("name", "pk")
        permissions = (
            (
                AppPermission.MANAGE_APPS.codename,
                "Manage apps",
            ),
            (
                AppPermission.MANAGE_OBSERVABILITY.codename,
                "Manage observability",
            ),
        )

    def __str__(self):
        return self.name

    def get_permissions(self) -> set[str]:
        """Return the permissions of the app."""
        if not self.is_active:
            return set()
        perm_cache_name = "_app_perm_cache"
        if not hasattr(self, perm_cache_name):
            perms = self.permissions.all()
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(self, perm_cache_name, {f"{ct}.{name}" for ct, name in perms})
        return getattr(self, perm_cache_name)

    def has_perms(self, perm_list: Iterable[Union[BasePermissionEnum, str]]) -> bool:
        """Return True if the app has each of the specified permissions."""
        if not self.is_active:
            return False

        wanted_perms = {
            perm.value if isinstance(perm, BasePermissionEnum) else perm
            for perm in perm_list
        }
        actual_perms = self.get_permissions()

        return (wanted_perms & actual_perms) == wanted_perms

    def has_perm(self, perm: Union[BasePermissionEnum, str]) -> bool:
        """Return True if the app has the specified permission."""
        if not self.is_active:
            return False

        perm_value = perm.value if isinstance(perm, BasePermissionEnum) else perm
        return perm_value in self.get_permissions()


class AppTokenManager(models.Manager["AppToken"]):
    def create(self, app, name="", auth_token=None, **extra_fields):
        """Create an app token with the given name."""
        if not auth_token:
            auth_token = generate_token()
        app_token = self.model(app=app, name=name, **extra_fields)
        app_token.set_auth_token(auth_token)
        app_token.save()
        return app_token, auth_token

    def create_with_token(self, *args, **kwargs) -> tuple["AppToken", str]:
        # As `create` is waiting to be fixed, I'm using this proper method from future
        # to get both AppToken and auth_token.
        return self.create(*args, **kwargs)


class AppToken(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name="tokens")
    name = models.CharField(blank=True, default="", max_length=128)
    auth_token = models.CharField(unique=True, max_length=128)
    token_last_4 = models.CharField(max_length=4)

    objects = AppTokenManager()

    def set_auth_token(self, raw_token=None):
        self.auth_token = make_password(raw_token)
        self.token_last_4 = raw_token[-4:]


class AppExtension(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name="extensions")
    label = models.CharField(max_length=256)
    url = models.URLField()
    mount = models.CharField(choices=AppExtensionMount.CHOICES, max_length=256)
    target = models.CharField(
        choices=AppExtensionTarget.CHOICES,
        max_length=128,
        default=AppExtensionTarget.POPUP,
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Specific permissions for this app extension.",
    )


class AppInstallation(Job):
    uuid = models.UUIDField(unique=True, default=uuid4)
    app_name = models.CharField(max_length=60)
    manifest_url = models.URLField()
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Specific permissions which will be assigned to app.",
        related_name="app_installation_set",
        related_query_name="app_installation",
    )
    brand_logo_default = models.ImageField(
        upload_to="app-installation-brand-data", blank=True, null=True
    )

    def set_message(self, message: str, truncate=True):
        if truncate:
            message_field = cast(models.Field, self._meta.get_field("message"))
            max_length = message_field.max_length
            if max_length is None:
                raise ValueError("Cannot truncate message without max_length")
            message = Truncator(message).chars(max_length)
        self.message = message
