from django.db import models
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from versatileimagefield.fields import PPOIField, VersatileImageField

from ..core.utils.translations import TranslationProxy
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from ..account.validators import validate_possible_number
from mptt.managers import TreeManager
from ..core.utils.editorjs import clean_editor_js
from ..core.db.fields import SanitizedJSONField
from ..core.models import ModelWithMetadata, SortableModel
from ..seo.models import SeoModel, SeoModelTranslation
from django.utils import timezone
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..account.models import User


class PossiblePhoneNumberField(PhoneNumberField):
    """Less strict field for phone numbers written to database."""
    default_validators = [validate_possible_number]

class StoreType(ModelWithMetadata, MPTTModel, SeoModel):
    name = models.CharField(max_length=250)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )

    objects = models.Manager()
    tree = TreeManager()
    translated = TranslationProxy()

    def __str__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

class StoreTypeTranslation(SeoModelTranslation):
    language_code = models.CharField(max_length=10)
    store_type = models.ForeignKey(
        StoreType, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        unique_together = (("language_code", "store_type"),)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        class_ = type(self)
        return "%s(pk=%r, name=%r, store_type_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
        )

class StoresQueryset(models.QuerySet):
    def visible_to_user(self, requestor: Union["User", "App"]):
        try:
            if requestor.is_superuser:
                return self.all()

            store_pk = requestor.store_id
            return self.filter(pk=store_pk)
        except:
            return None

class Store(models.Model):
    name = models.CharField(max_length=250)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    store_type = models.ForeignKey(
        StoreType,
        related_name="stores",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    phone = PossiblePhoneNumberField(blank=True, default="")
    acreage = models.FloatField(blank=True, null=True, max_length=250)
    latlong = models.CharField(blank=True, null=True, max_length=250)
    background_image = VersatileImageField(
        upload_to="store-backgrounds", blank=True, null=True
    )
    background_image_alt = models.CharField(max_length=128, blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)

    objects = StoresQueryset.as_manager()
    translated = TranslationProxy()


    def __str__(self) -> str:
        return self.name

class StoreTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    store = models.ForeignKey(
        Store, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)

    class Meta:
        unique_together = (("language_code", "store"),)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        class_ = type(self)
        return "%s(pk=%r, name=%r, category_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.name,
            self.store_id,
        )