from django import forms
from django.urls import reverse_lazy
from django.utils.translation import pgettext_lazy

from ...menu.models import Menu, MenuItem
from ...page.models import Page
from ...product.models import Category, Collection
from ..forms import (
    AjaxSelect2CombinedChoiceField, OrderedModelMultipleChoiceField)


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ('slug',)
        labels = {
            'slug': pgettext_lazy('Menu internal name', 'Internal name')}


class MenuItemForm(forms.ModelForm):
    linked_object = AjaxSelect2CombinedChoiceField(
        querysets=[
            Collection.objects.all(), Category.objects.all(),
            Page.objects.all()],
        fetch_data_url=reverse_lazy('dashboard:ajax-menu-links'))

    class Meta:
        model = MenuItem
        fields = ('name',)
        labels = {
            'name': pgettext_lazy('Menu item name', 'Name'),
            'linked_object': pgettext_lazy('Menu item name', 'Link')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        destination = self.instance.destination

        if destination:
            self.fields['linked_object'].set_initial(
                destination, self.instance.get_destination_display())

    def save(self, commit=True):
        linked_object = self.cleaned_data.get('linked_object')

        if linked_object.__class__ == Collection:
            self.instance.collection = linked_object
        elif linked_object.__class__ == Category:
            self.instance.category = linked_object
        elif linked_object.__class__ == Page:
            self.instance.page = linked_object

        self.instance.url = linked_object.get_absolute_url()
        return super().save(commit)


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
