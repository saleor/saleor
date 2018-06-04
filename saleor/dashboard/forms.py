import json

from django import forms
from django.core.exceptions import ValidationError


class ModelChoiceOrCreationField(forms.ModelChoiceField):
    """ModelChoiceField with the ability to create new choices.

    This field allows to select values from a queryset, but it also accepts
    new values that can be used to create new model choices.
    """

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            obj = self.queryset.get(**{key: value})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            return value
        else:
            return obj


class OrderedModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def clean(self, value):
        qs = super().clean(value)
        keys = list(map(int, value))
        return sorted(qs, key=lambda v: keys.index(v.pk))


class AjaxSelect2ChoiceField(forms.ChoiceField):
    """An AJAX-based choice field using Select2.

    fetch_data_url - specifies url, from which select2 will fetch data
    initial - initial object
    """

    def __init__(
            self, fetch_data_url='', initial=None, min_input=2, *args,
            **kwargs):
        self.queryset = kwargs.pop('queryset', None)
        super().__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'enable-ajax-select2'
        self.widget.attrs['data-url'] = fetch_data_url
        self.widget.attrs['data-min-input'] = min_input
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

    def set_initial(self, obj, obj_id=None, label=None):
        """Set initially selected objects on field's widget."""
        selected = {
            'id': obj_id if obj_id is not None else obj.pk,
            'text': label if label else str(obj)}
        self.widget.attrs['data-initial'] = json.dumps(selected)

    def set_fetch_data_url(self, fetch_data_url):
        self.widget.attrs['data-url'] = fetch_data_url


class AjaxSelect2CombinedChoiceField(AjaxSelect2ChoiceField):
    """An AJAX-based choice field using Select2 for multiple querysets.

    Value passed to a field is of format '<obj.id>_<obj.__class__.__name__>',
    e. g. '17_Collection' for Collection object with id 17.

    fetch_data_url - specifies url, from which select2 will fetch data
    initial - initial object
    """

    def __init__(self, *args, **kwargs):
        self.querysets = kwargs.pop('querysets')
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None

        pk, model_name = value.split('_')
        queryset = next(
            (qs for qs in self.querysets if qs.model.__name__ == model_name),
            None)

        value = queryset.filter(pk=pk).first() if queryset else None

        if not value:
            raise forms.ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice')
        return value


class AjaxSelect2MultipleChoiceField(forms.MultipleChoiceField):
    """An AJAX-base multiple choice field using Select2.

    fetch_data_url - specifies url, from which select2 will fetch data
    initial - list of initial objects
    """

    def __init__(
            self, fetch_data_url='', initial=[], min_input=2, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super().__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'enable-ajax-select2'
        self.widget.attrs['data-url'] = fetch_data_url
        self.widget.attrs['data-min-input'] = min_input
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


class PermissionMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ Permission multiple choice field with label override."""

    def label_from_instance(self, obj):
        return obj.name
