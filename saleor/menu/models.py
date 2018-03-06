from django.db import models
from django.db.models import Max
from django.utils.translation import pgettext_lazy
from mptt.managers import TreeManager
from mptt.models import MPTTModel


class Menu(models.Model):
    slug = models.SlugField(max_length=50)

    class Meta:
        permissions = (
            ('view_menu',
             pgettext_lazy('Permission description', 'Can view menus')),
            ('edit_menu',
             pgettext_lazy('Permission description', 'Can edit menus')))

    def __str__(self):
        return self.slug


class MenuItem(MPTTModel):
    menu = models.ForeignKey(
        Menu, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    sort_order = models.PositiveIntegerField(editable=False)
    url = models.URLField(max_length=256)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)

    objects = models.Manager()
    tree = TreeManager()

    class Meta:
        ordering = ('sort_order',)
        app_label = 'menu'

    def __str__(self):
        return self.name

    def get_ordering_queryset(self):
        return (
            self.menu.items.all() if not self.parent
            else self.parent.children.all())

    def save(self, *args, **kwargs):
        if self.sort_order is None:
            qs = self.get_ordering_queryset()
            existing_max = qs.aggregate(Max('sort_order'))
            existing_max = existing_max.get('sort_order__max')
            self.sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)
