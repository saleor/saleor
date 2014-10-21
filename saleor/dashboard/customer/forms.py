from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class CustomerSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_('Email'))
    name = forms.CharField(required=False, label=_('Name'))

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super(CustomerSearchForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        if not any(data.values()):
            raise forms.ValidationError(
                _('At least one field must be specified'), code='invalid')
        for field in data.keys():
            data[field] = data[field].strip()
        return data

    def search(self):
        queryset = self.queryset
        data = self.cleaned_data
        if data['email']:
            queryset = queryset.filter(email__icontains=data['email'])
        if data['name']:
            parts = data['name'].split()
            if len(parts) == 2:
                query = ((Q(addresses__first_name__icontains=parts[0]) |
                          Q(addresses__last_name__icontains=parts[1])) |
                         (Q(addresses__first_name__icontains=parts[1]) |
                          Q(addresses__last_name__icontains=parts[0])))
            else:
                query = (Q(addresses__first_name__icontains=data['name']) |
                         Q(addresses__last_name__icontains=data['name']))
            queryset = queryset.filter(query).distinct()
        return queryset
