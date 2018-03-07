from django import forms
from django.utils.translation import pgettext_lazy

from ...menu.models import Menu, MenuItem
from ..forms import OrderedModelMultipleChoiceField


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


class ReorderMenuItemsForm(forms.ModelForm):
    ordered_menu_items = OrderedModelMultipleChoiceField(
        queryset=MenuItem.objects.none())

    class Meta:
        model = Menu
        fields = ()

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)
        qs = (
            self.parent.get_descendants() if self.parent
            else self.instance.items.filter(parent=None))
        self.fields['ordered_menu_items'].queryset = qs

    def save(self):
        for sort_order, menu_item in enumerate(
                self.cleaned_data['ordered_menu_items']):
            menu_item.sort_order = sort_order
            menu_item.save()
        return self.instance
