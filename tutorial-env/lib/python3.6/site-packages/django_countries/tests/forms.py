from django import forms

from django_countries.tests import models


class PersonForm(forms.ModelForm):
    class Meta:
        model = models.Person
        fields = ["country", "favourite_country"]


class AllowNullForm(forms.ModelForm):
    class Meta:
        model = models.AllowNull
        fields = ["country"]


class MultiCountryForm(forms.ModelForm):
    class Meta:
        model = models.MultiCountry
        fields = ["countries"]
