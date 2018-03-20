from django import forms
from django.urls import reverse_lazy
from django.utils.translation import pgettext_lazy

from ...menu.models import Menu, MenuItem
from ...page.models import Page
from ...product.models import Category, Collection
from ..forms import (
    AjaxSelect2CombinedChoiceField, OrderedModelMultipleChoiceField)


class MenuForm(forms.ModelForm):
    """Add or update menu."""

    class Meta:
        model = Menu
        fields = ('slug',)
        labels = {
            'slug': pgettext_lazy('Menu internal name', 'Internal name')}


class MenuItemForm(forms.ModelForm):
    """Add or update menu item.

    An item can point to a URL passed directly or to an object belonging
    to one of querysets passed to a linked_object field.

    linked_object value passed to a field requires format
    '<obj.id>_<obj.__class__.__name__>', e. g. '17_Collection' for Collection
    object with id 17.
    """

    linked_object = AjaxSelect2CombinedChoiceField(
        querysets=[
            Collection.objects.all(), Category.objects.all(),
            Page.objects.all()],
        fetch_data_url=reverse_lazy('dashboard:ajax-menu-links'), min_input=0,
        required=False)

    class Meta:
        model = MenuItem
        fields = ('name', 'url')
        labels = {
            'name': pgettext_lazy('Menu item name', 'Name'),
            'url': pgettext_lazy('Menu item url', 'URL'),
            'linked_object': pgettext_lazy('Menu item object to link', 'Link')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        obj = self.instance.linked_object
        if obj:
            obj_id = str(obj.pk) + '_' + obj.__class__.__name__
            self.fields['linked_object'].set_initial(obj, obj_id=obj_id)

    def clean(self):
        parent = self.instance.parent
        if parent and parent.level >= 2:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Menu item form error',
                    'Maximum nesting level for menu items equals to 2.'),
                code='invalid')
        url = self.cleaned_data.get('url')
        linked_object = self.cleaned_data.get('linked_object')
        if url and linked_object:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Menu item form error',
                    'A single menu item can\'t point to both an internal link '
                    'and URL.'),
                code='invalid')
        if not url and not linked_object:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Menu item form error',
                    'A single menu item must point to an internal link or '
                    'URL.'),
                code='invalid')
        return self.cleaned_data

    def save(self, commit=True):
        linked_object = self.cleaned_data.get('linked_object')

        if isinstance(linked_object, Collection):
            self.instance.collection = linked_object
        elif isinstance(linked_object, Category):
            self.instance.category = linked_object
        elif isinstance(linked_object, Page):
            self.instance.page = linked_object

        return super().save(commit)


class ReorderMenuItemsForm(forms.ModelForm):
    """Reorder menu items.

    Args:
        ordered_menu_items - sorted menu items
    """

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
