from django import forms


class CaptureForm(forms.Form):
    amount = forms.DecimalField()
