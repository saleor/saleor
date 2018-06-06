from django import forms

from ...menu.models import Menu, MenuItem


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name']


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'menu', 'name', 'parent', 'url', 'category', 'collection', 'page']
