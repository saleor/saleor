from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import pgettext_lazy
from mptt.managers import TreeManager
from mptt.models import MPTTModel

from ..core.models import SortableModel
from ..core.utils.translations import TranslationProxy
from ..page.models import Page
from ..product.models import Category, Collection


class Menu(models.Model):
    name = models.CharField(max_length=128)
    json_content = JSONField(blank=True, default=dict)

    class Meta:
        ordering = ('pk', )
        permissions = ((
            'manage_menus',
            pgettext_lazy('Permission description', 'Manage navigation.')), )

    def __str__(self):
        return self.name


class MenuItem(MPTTModel, SortableModel):
    menu = models.ForeignKey(
        Menu, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)

    # not mandatory fields, usage depends on what type of link is stored
    url = models.URLField(max_length=256, blank=True, null=True)
    category = models.ForeignKey(
        Category, blank=True, null=True, on_delete=models.CASCADE)
    collection = models.ForeignKey(
        Collection, blank=True, null=True, on_delete=models.CASCADE)
    page = models.ForeignKey(
        Page, blank=True, null=True, on_delete=models.CASCADE)

    objects = models.Manager()
    tree = TreeManager()
    translated = TranslationProxy()

    class Meta:
        ordering = ('sort_order', )
        app_label = 'menu'

    def __str__(self):
        return self.name

    def get_ordering_queryset(self):
        return (
            self.menu.items.all() if not self.parent
            else self.parent.children.all())

    @property
    def linked_object(self):
        return self.category or self.collection or self.page

    @property
    def destination_display(self):
        linked_object = self.linked_object

        if not linked_object:
            prefix = pgettext_lazy('Link object type description', 'URL: ')
            return prefix + self.url

        if isinstance(linked_object, Category):
            prefix = pgettext_lazy(
                'Link object type description', 'Category: ')
        elif isinstance(linked_object, Collection):
            prefix = pgettext_lazy(
                'Link object type description', 'Collection: ')
        else:
            prefix = pgettext_lazy(
                'Link object type description', 'Page: ')

        return prefix + str(linked_object)

    def get_url(self):
        linked_object = self.linked_object
        return linked_object.get_absolute_url() if linked_object else self.url

    def is_public(self):
        return not self.linked_object or getattr(
            self.linked_object, 'is_published', True)


class MenuItemTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    menu_item = models.ForeignKey(
        MenuItem, related_name='translations', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    class Meta:
        unique_together = (('language_code', 'menu_item'),)

    def __repr__(self):
        class_ = type(self)
        return '%s(pk=%r, name=%r, menu_item_pk=%r)' % (
            class_.__name__, self.pk, self.name, self.menu_item_id)

    def __str__(self):
        return self.name
