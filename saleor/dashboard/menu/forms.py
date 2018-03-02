from django import forms
from django.utils.translation import pgettext_lazy

from ...menu.models import Menu, MenuItem


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ('slug',)
        labels = {
            'slug': pgettext_lazy('Menu internal name', 'Internal name')}


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ('name', 'url')
        labels = {
            'name': pgettext_lazy('Menu item name', 'Name'),
            'sort_order': pgettext_lazy('Menu item name', 'Sorting order'),
            'url': pgettext_lazy('Menu item name', 'URL')}
