from __future__ import unicode_literals

from django import forms
from django.utils.translation import pgettext_lazy

from .models import Wishlist

ACCESS_CHOICES = (
    (True, pgettext_lazy('wishlist form', 'Public - anyone with url')),
    (False, pgettext_lazy('wishlist form', 'Private - only you')))


class WishlistSettingsForm(forms.ModelForm):
    generate = forms.BooleanField(initial=False, required=False,
                                  label=pgettext_lazy('wishlist form',
                                                      'Generate new url'))

    class Meta:
        model = Wishlist
        fields = ['public']
        labels = {'public': pgettext_lazy('wishlist form', 'Wishlist access')}
        widgets = {'public': forms.Select(choices=ACCESS_CHOICES)}

    def save(self, commit=True):
        obj = super(WishlistSettingsForm, self).save(commit=False)

        if self.cleaned_data['generate'] and hasattr(obj, 'instance'):
            obj.instance.change_token()
        if commit:
            obj.save()
        return obj

