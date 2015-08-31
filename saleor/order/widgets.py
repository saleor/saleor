from django import forms
from django.template.loader import render_to_string


class ButtonSelect(forms.RadioSelect):
    def render(self, name, value, attrs=None, choices=()):
        if not choices:
            choices = self.choices
        return render_to_string('order/includes/choices.html', {
            'value': value, 'choices': choices})
