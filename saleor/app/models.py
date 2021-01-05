from typing import Set

from django.contrib.auth.models import Permission
from django.db import models
from oauthlib.common import generate_token

from ..core.models import Job, ModelWithMetadata
from ..core.permissions import AppPermission
from .types import AppType


class App(ModelWithMetadata):
    name = models.CharField(max_length=60)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    type = models.CharField(
        choices=AppType.CHOICES, default=AppType.LOCAL, max_length=60
    )
    identifier = models.CharField(blank=True, null=True, max_length=256)
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
    version = models.CharField(max_length=60, blank=True, null=True)

    class Meta:
        ordering = ("name", "pk")
        permissions = (
            (
                AppPermission.MANAGE_APPS.codename,
                "Manage apps",
            ),
        )

    def get_permissions(self) -> Set[str]:
        """Return the permissions of the app."""
        if not self.is_active:
            return set()
        perm_cache_name = "_app_perm_cache"
        if not hasattr(self, perm_cache_name):
            perms = self.permissions.all()
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(self, perm_cache_name, {f"{ct}.{name}" for ct, name in perms})
        return getattr(self, perm_cache_name)

    def has_perms(self, perm_list):
        """Return True if the app has each of the specified permissions."""
        if not self.is_active:
            return False

        try:
            wanted_perms = {perm.value for perm in perm_list}
        except AttributeError:
            wanted_perms = set(perm_list)
        actual_perms = self.get_permissions()

        return (wanted_perms & actual_perms) == wanted_perms

    def has_perm(self, perm):
        """Return True if the app has the specified permission."""
        if not self.is_active:
            return False

        perm_value = perm.value if hasattr(perm, "value") else perm
        return perm_value in self.get_permissions()


class AppToken(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name="tokens")
    name = models.CharField(blank=True, default="", max_length=128)
    auth_token = models.CharField(default=generate_token, unique=True, max_length=30)


class AppInstallation(Job):
    app_name = models.CharField(max_length=60)
    manifest_url = models.URLField()
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Specific permissions which will be assigned to app.",
        related_name="app_installation_set",
        related_query_name="app_installation",
    )
