import datetime
import re

from django.conf import settings
from django.forms.extras.widgets import _parse_date_fmt, RE_DATE
from django.forms.widgets import Widget, Select, TextInput
from django.utils import datetime_safe
from django.utils.formats import get_format
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
import time

class SelectMonthWidget(Widget):
    """
    A Widget that splits date input into two <select> boxes.
    """
    month_field = '%s_month'
    year_field = '%s_year'

    def __init__(self, attrs=None, years=None, required=True):
        # years is an optional list/tuple of years to use in the "year" select box.
        self.attrs = attrs or {}
        self.required = required
        if years:
            self.years = years
        else:
            this_year = datetime.date.today().year
            self.years = range(this_year, this_year+10)

    def render(self, name, value, attrs=None):
        try:
            year_val, month_val = value.year, value.month
        except AttributeError:
            year_val = month_val = None
            if isinstance(value, basestring):
                if settings.USE_L10N:
                    try:
                        input_format = get_format('DATE_INPUT_FORMATS')[0]
                        v = datetime.datetime.strptime(value, input_format)
                        year_val, month_val = v.year, v.month
                    except ValueError:
                        pass
                else:
                    match = RE_DATE.match(value)
                    if match:
                        year_val, month_val, day_val = [int(v) for v in match.groups()]
        choices = [(i, i) for i in self.years]
        year_html = self.create_select(name, self.year_field, value, year_val,
                                       choices, none_value=(0, _('Year')))
        choices = [(i, '%02d' % i) for i in range(1,13)]
        month_html = self.create_select(name, self.month_field, value, month_val,
                                        choices, none_value=(0, _('Month')))

        output = []
        for field in _parse_date_fmt():
            if field == 'year':
                output.append(year_html)
            elif field == 'month':
                output.append(month_html)
        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        first_select = None
        field_list = _parse_date_fmt()
        if field_list:
            first_select = field_list[0]
        if first_select is not None:
            return '%s_%s' % (id_, first_select)
        else:
            return '%s_month' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        if y == m == "0":
            return None
        if y and m:
            if settings.USE_L10N:
                input_format = get_format('DATE_INPUT_FORMATS')[0]
                try:
                    date_value = datetime.date(int(y), int(m), 1)
                except ValueError:
                    return '%s-%s-%s' % (y, m, 1)
                else:
                    date_value = datetime_safe.new_date(date_value)
                    return date_value.strftime(input_format)
            else:
                return '%s-%s-%s' % (y, m, 1)
        return data.get(name, None)

    def create_select(self, name, field, value, val, choices, none_value):
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        if not (self.required and val):
            choices.insert(0, none_value)
        local_attrs = self.build_attrs(id=field % id_)
        s = Select(choices=choices)
        select_html = s.render(field % name, val, local_attrs)
        return select_html

class CreditCardNumberWidget(TextInput):
    def render(self, name, value, attrs):
        if value:
            value = re.sub('[\s-]', '', value)
            value = ' '.join([value[i:i+4] for i in range(0, len(value), 4)])
        return super(CreditCardNumberWidget, self).render(name, value, attrs)
