from __future__ import unicode_literals


def get_sort_by_choices(filter):
    return [(choice[0], choice[1].lower()) for choice in
            filter.filters['sort_by'].field.choices[1::2]]


def get_now_sorted_by(filter, fields):
    sort_by = filter.form.cleaned_data.get('sort_by')
    if sort_by:
        sort_by = fields[sort_by[0].strip('-')]
    else:
        sort_by = fields['name']
    return sort_by
