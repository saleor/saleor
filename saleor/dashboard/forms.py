import json

from django import forms
from django.core.exceptions import ValidationError


class AjaxSelect2ChoiceField(forms.ChoiceField):
    """An AJAX-based choice field using Select2.

    fetch_data_url - specifies url, from which select2 will fetch data
    initial - initial object
    """

    def __init__(self, fetch_data_url='', initial=None, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super().__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'enable-ajax-select2'
        self.widget.attrs['data-url'] = fetch_data_url
        if initial:
            self.set_initial(initial)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            value = self.queryset.get(pk=value)
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            raise forms.ValidationError(
                self.error_messages['invalid_choice'], code='invalid_choice')
        return value

    def valid_value(self, value):
        forms.Field.validate(self, value)
        return True

    def set_initial(self, obj):
        """Set initially selected objects on field's widget."""
        selected = {'id': obj.pk, 'text': str(obj)}
        self.widget.attrs['data-initial'] = json.dumps(selected)


class AjaxSelect2MultipleChoiceField(forms.MultipleChoiceField):
    """An AJAX-base multiple choice field using Select2.

    fetch_data_url - specifies url, from which select2 will fetch data
    initial - list of initial objects
    """

    def __init__(self, fetch_data_url='', initial=[], *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super().__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'enable-ajax-select2'
        self.widget.attrs['data-url'] = fetch_data_url
        if initial:
            self.set_initial(initial)
        self.widget.attrs['multiple'] = True

    def to_python(self, value):
        # Allow to set empty field
        if value == []:
            return value
        if value in self.empty_values:
            return None
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(
                self.error_messages['invalid_list'], code='invalid_list')
        for choice in value:
            try:
                self.queryset.get(pk=choice)
            except (ValueError, TypeError, self.queryset.model.DoesNotExist):
                raise forms.ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice')
        return [str(val) for val in value]

    def valid_value(self, value):
        forms.Field.validate(self, value)
        return True

    def set_initial(self, objects):
        """Set initially selected objects on field's widget."""
        selected = [{'id': obj.pk, 'text': str(obj)} for obj in objects]
        self.widget.attrs['data-initial'] = json.dumps(selected)
