from django import forms


class AjaxSelect2ChoiceField(forms.ChoiceField):

    def __init__(self, fetch_data_url='', initial=None, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super(AjaxSelect2ChoiceField, self).__init__(*args, **kwargs)
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

    def set_fetch_data_url(self, url):
        self.widget.attrs['data-url'] = url

    def set_initial(self, obj):
        self.widget.attrs['data-initial-display'] = str(obj)
        self.widget.attrs['data-initial-value'] = obj.pk
