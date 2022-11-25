from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class PermissionManager(models.Manager):
    use_in_migrations = True

    def get_by_natural_key(self, codename, app_label, model):
        return self.get(
            codename=codename,
            content_type=ContentType.objects.db_manager(self.db).get_by_natural_key(
                app_label, model
            ),
        )


class Permission(models.Model):
    """The system provides a way to assign permissions to users and groups of users.

    The permission system is used by the Django admin site, but may also be
    useful in your own code. The Django admin site uses permissions as follows:

        - The "add" permission limits the user's ability to view the "add" form
          and add an object.
        - The "change" permission limits a user's ability to view the change
          list, view the "change" form and change an object.
        - The "delete" permission limits the ability to delete an object.
        - The "view" permission limits the ability to view an object.

    Permissions are set globally per type of object, not per specific object
    instance. It is possible to say "Mary may change news stories," but it's
    not currently possible to say "Mary may change news stories, but only the
    ones she created herself" or "Mary may only change news stories that have a
    certain status or publication date."

    The permissions listed above are automatically created for each model.
    """

    name = models.CharField(_("name"), max_length=255)
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
        verbose_name=_("content type"),
        # TODO Owczar: Remove related_name after drop django auth.
        related_name="saleor_content_type",
    )
    codename = models.CharField(_("codename"), max_length=100)

    objects = PermissionManager()

    class Meta:
        verbose_name = _("permission")
        verbose_name_plural = _("permissions")
        unique_together = [["content_type", "codename"]]
        ordering = ["content_type__app_label", "content_type__model", "codename"]

    def __str__(self):
        return "%s | %s" % (self.content_type, self.name)

    def natural_key(self):
        return (self.codename,) + self.content_type.natural_key()

    natural_key.dependencies = ["contenttypes.contenttype"]  # type: ignore
