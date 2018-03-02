from django import forms
from django.utils.translation import pgettext_lazy

from ...menu.models import Menu


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ('slug',)
        labels = {
            'slug': pgettext_lazy('Menu internal name', 'Internal name')}
